/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.apache.lucene.demo;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.analysis.th.ThaiAnalyzer;
import org.apache.lucene.demo.knn.DemoEmbeddings;
import org.apache.lucene.demo.knn.KnnVectorDict;
import org.apache.lucene.document.*;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.index.IndexWriterConfig.OpenMode;
import org.apache.lucene.index.Term;
import org.apache.lucene.index.VectorSimilarityFunction;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.IOUtils;
import org.apache.lucene.benchmark.byTask.feeds.DemoHTMLParser.Parser;
import org.xml.sax.SAXException;

/**
 * Index all text files under a directory.
 *
 * <p>This is a command-line application demonstrating simple Lucene indexing. Run it with no
 * command-line arguments for usage information.
 */
public class IndexFilesWithMoreInfo implements AutoCloseable {
  static final String KNN_DICT = "knn-dict";

  // Calculates embedding vectors for KnnVector search
  private final DemoEmbeddings demoEmbeddings;
  private final KnnVectorDict vectorDict;
  private final List<String> provinces = Arrays.asList(
          "เชียงราย", "เชียงใหม่", "น่าน", "พะเยา", "แพร่", "แม่ฮ่องสอน", "ลำปาง", "ลำพูน", "อุตรดิตถ์",
          "กำแพงเพชร", "พิจิตร", "พิษณุโลก", "เพชรบูรณ์", "สุโขทัย", "อุทัยธานี", "นครสวรรค์",
          "กาฬสินธุ์", "ขอนแก่น", "ชัยภูมิ", "นครพนม", "นครราชสีมา", "บึงกาฬ", "บุรีรัมย์", "มหาสารคาม",
          "มุกดาหาร", "ยโสธร", "ร้อยเอ็ด", "ศรีสะเกษ", "สกลนคร", "สุรินทร์", "หนองคาย", "หนองบัวลำภู",
          "อำนาจเจริญ", "อุดรธานี", "อุบลราชธานี", "กาญจนบุรี", "นครปฐม", "ประจวบคีรีขันธ์", "เพชรบุรี",
          "ราชบุรี", "สมุทรสงคราม", "สมุทรสาคร", "สุพรรณบุรี", "จันทบุรี", "ฉะเชิงเทรา", "ชลบุรี", "ตราด",
          "ปราจีนบุรี", "ระยอง", "สระแก้ว", "กรุงเทพ", "นครนายก", "นนทบุรี", "ปทุมธานี", "พระนครศรีอยุธยา",
          "สมุทรปราการ", "สระบุรี", "อ่างทอง", "ชัยนาท", "ลพบุรี", "นครศรีธรรมราช", "กระบี่", "ชุมพร",
          "ตรัง", "นครศรีธรรมราช", "นราธิวาส", "ปัตตานี", "พังงา", "พัทลุง", "ภูเก็ต", "ยะลา", "ระนอง",
          "สงขลา", "สตูล", "สุราษฎร์ธานี"
  );

  private IndexFilesWithMoreInfo(KnnVectorDict vectorDict) throws IOException {
    if (vectorDict != null) {
      this.vectorDict = vectorDict;
      demoEmbeddings = new DemoEmbeddings(vectorDict);
    } else {
      this.vectorDict = null;
      demoEmbeddings = null;
    }
  }

  private static Path docDir;

  /** Index all text files under a directory. */
  public static void main(String[] args) throws Exception {
    String usage =
        "java org.apache.lucene.demo.IndexFiles"
            + " [-index INDEX_PATH] [-docs DOCS_PATH] [-update] [-knn_dict DICT_PATH]\n\n"
            + "This indexes the documents in DOCS_PATH, creating a Lucene index "
            + "in INDEX_PATH that can be searched with SearchFiles\n"
            + "IF DICT_PATH contains a KnnVector dictionary, the index will also support KnnVector search";
    String indexPath = "index";
    String docsPath = null;
    String vectorDictSource = null;
    boolean create = true;
    for (int i = 0; i < args.length; i++) {
      switch (args[i]) {
        case "-index":
          indexPath = args[++i];
          break;
        case "-docs":
          docsPath = args[++i];
          break;
        case "-knn_dict":
          vectorDictSource = args[++i];
          break;
        case "-update":
          create = false;
          break;
        case "-create":
          create = true;
          break;
        default:
          throw new IllegalArgumentException("unknown parameter " + args[i]);
      }
    }

    if (docsPath == null) {
      System.err.println("Usage: " + usage);
      System.exit(1);
    }

//    final Path docDir = Paths.get(docsPath);
    docDir = Paths.get(docsPath);
    if (!Files.isReadable(docDir)) {
      System.out.println(
          "Document directory '"
              + docDir.toAbsolutePath()
              + "' does not exist or is not readable, please check the path");
      System.exit(1);
    }

    Date start = new Date();
    try {
      System.out.println("Indexing to directory '" + indexPath + "'...");

      Directory dir = FSDirectory.open(Paths.get(indexPath));
      Analyzer analyzer = new ThaiAnalyzer();
      IndexWriterConfig iwc = new IndexWriterConfig(analyzer);

      if (create) {
        // Create a new index in the directory, removing any
        // previously indexed documents:
        iwc.setOpenMode(OpenMode.CREATE);
      } else {
        // Add new documents to an existing index:
        iwc.setOpenMode(OpenMode.CREATE_OR_APPEND);
      }

      // Optional: for better indexing performance, if you
      // are indexing many documents, increase the RAM
      // buffer.  But if you do this, increase the max heap
      // size to the JVM (e.g. add -Xmx512m or -Xmx1g):
      //
      // iwc.setRAMBufferSizeMB(256.0);

      KnnVectorDict vectorDictInstance = null;
      long vectorDictSize = 0;
      if (vectorDictSource != null) {
        KnnVectorDict.build(Paths.get(vectorDictSource), dir, KNN_DICT);
        vectorDictInstance = new KnnVectorDict(dir, KNN_DICT);
        vectorDictSize = vectorDictInstance.ramBytesUsed();
      }

      try (IndexWriter writer = new IndexWriter(dir, iwc);
          IndexFilesWithMoreInfo indexFiles = new IndexFilesWithMoreInfo(vectorDictInstance)) {
        indexFiles.indexDocs(writer, docDir);

        // NOTE: if you want to maximize search performance,
        // you can optionally call forceMerge here.  This can be
        // a terribly costly operation, so generally it's only
        // worth it when your index is relatively static (ie
        // you're done adding documents to it):
        //
        // writer.forceMerge(1);
      } finally {
        IOUtils.close(vectorDictInstance);
      }

      Date end = new Date();
      try (IndexReader reader = DirectoryReader.open(dir)) {
        System.out.println(
            "Indexed "
                + reader.numDocs()
                + " documents in "
                + (end.getTime() - start.getTime())
                + " ms");
        if (Objects.isNull(vectorDictSource) == false
            && reader.numDocs() > 100
            && vectorDictSize < 1_000_000
            && System.getProperty("smoketester") == null) {
          throw new RuntimeException(
              "Are you (ab)using the toy vector dictionary? See the package javadocs to understand why you got this exception.");
        }
      }
    } catch (IOException e) {
      System.out.println(" caught a " + e.getClass() + "\n with message: " + e.getMessage());
    }
  }

  /**
   * Indexes the given file using the given writer, or if a directory is given, recurses over files
   * and directories found under the given directory.
   *
   * <p>NOTE: This method indexes one document per input file. This is slow. For good throughput,
   * put multiple documents into your input file(s). An example of this is in the benchmark module,
   * which can create "line doc" files, one document per line, using the <a
   * href="../../../../../contrib-benchmark/org/apache/lucene/benchmark/byTask/tasks/WriteLineDocTask.html"
   * >WriteLineDocTask</a>.
   *
   * @param writer Writer to the index where the given file/dir info will be stored
   * @param path The file to index, or the directory to recurse into to find files to index
   * @throws IOException If there is a low-level I/O error
   */
  void indexDocs(final IndexWriter writer, Path path) throws IOException {
    if (Files.isDirectory(path)) {
      Files.walkFileTree(
          path,
          new SimpleFileVisitor<>() {
            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
              try {
                indexDoc(writer, file, attrs.lastModifiedTime().toMillis());
              } catch (
                  @SuppressWarnings("unused")
                  IOException ignore) {
                ignore.printStackTrace(System.err);
                // don't index files that can't be read.
              }
              return FileVisitResult.CONTINUE;
            }
          });
    } else {
      indexDoc(writer, path, Files.getLastModifiedTime(path).toMillis());
    }
  }

  /** Indexes a single document */
  void indexDoc(IndexWriter writer, Path file, long lastModified) throws IOException {
    try (InputStream stream = Files.newInputStream(file)) {
      // make a new, empty document
      Document doc = new Document();

      // Add the path of the file as a field named "path".  Use a
      // field that is indexed (i.e. searchable), but don't tokenize
      // the field into separate words and don't index term frequency
      // or positional information:
      doc.add(new KeywordField("path", file.toString(), Field.Store.YES));

      // Add the last modified date of the file a field named "modified".
      // Use a LongField that is indexed with points and doc values, and is efficient
      // for both filtering (LongField#newRangeQuery) and sorting
      // (LongField#newSortField).  This indexes to millisecond resolution, which
      // is often too fine.  You could instead create a number based on
      // year/month/day/hour/minutes/seconds, down the resolution you require.
      // For example the long value 2011021714 would mean
      // February 17, 2011, 2-3 PM.
      doc.add(new LongField("modified", lastModified, Field.Store.NO));

      // Add the contents of the file to a field named "contents".  Specify a Reader,
      // so that the text of the file is tokenized and indexed, but not stored.
      // Note that FileReader expects the file to be in UTF-8 encoding.
      // If that's not the case searching for special characters will fail.
//      doc.add(
//          new TextField(
//              "contents",
//              new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))));
      // ***** Modified with These *****
      Parser parser = new Parser(new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8)));

      String title = parser.title;
      doc.add(new TextField("title", title, Field.Store.YES));

      String content = parser.body.replaceAll("\\s+", " ");
      doc.add(new TextField("contents", content, Field.Store.YES));

      Map<String, Integer> provinceCounts = new HashMap<>();
      for (String province : provinces) {
        Pattern pattern = Pattern.compile(province);
        Matcher matcher = pattern.matcher(content);

        int count = 0;
        while (matcher.find()) {
          count++;
        }

        // If the province appears at least once, store the count
        if (count > 0) {
          provinceCounts.put(province, count);
        }
      }

      // Add each province and its count to the document as well
      for (Map.Entry<String, Integer> entry : provinceCounts.entrySet()) {
        String provinceName = entry.getKey();
        int count = entry.getValue();

        // Adding each province and its count as a separate TextField
        doc.add(new TextField("province_" + provinceName, Integer.toString(count), Field.Store.YES));
      }

      String filePath = file.toString();
      String basePath = docDir.toString();

      String relativePath = filePath.substring(basePath.length() + 1).replace('\\', '/');

      String[] pathSegments = relativePath.split("/");

      if (pathSegments.length > 1) {
        relativePath = String.join("/", Arrays.copyOfRange(pathSegments, 1, pathSegments.length));
      }

      if (relativePath.endsWith("/dummy")) {
        relativePath = relativePath.substring(0, relativePath.lastIndexOf("/dummy"));
      }

      String url = "https://" + relativePath;
      doc.add(new StoredField("url", url));
      // *******************************

      if (demoEmbeddings != null) {
        try (InputStream in = Files.newInputStream(file)) {
          float[] vector =
              demoEmbeddings.computeEmbedding(
                  new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8)));
          doc.add(
              new KnnFloatVectorField(
                  "contents-vector", vector, VectorSimilarityFunction.DOT_PRODUCT));
        }
      }

      if (writer.getConfig().getOpenMode() == OpenMode.CREATE) {
        // New index, so we just add the document (no old document can be there):
        System.out.println("adding " + file);
        writer.addDocument(doc);
      } else {
        // Existing index (an old copy of this document may have been indexed) so
        // we use updateDocument instead to replace the old one matching the exact
        // path, if present:
        System.out.println("updating " + file);
        writer.updateDocument(new Term("path", file.toString()), doc);
      }
    } catch (SAXException e) {
//        throw new RuntimeException(e);
    }
  }

  @Override
  public void close() throws IOException {
    IOUtils.close(vectorDict);
  }
}
