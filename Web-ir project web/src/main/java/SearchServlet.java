import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.th.ThaiAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.*;
import org.apache.lucene.search.highlight.*;
import org.apache.lucene.store.FSDirectory;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

public static class SearchServlet extends HttpServlet {

    String indexName = indexLocation;       //local copy of the configuration variable
    try {
          IndexReader reader = DirectoryReader.open(FSDirectory.open(Paths.get(indexName)));
          searcher = new IndexSearcher(reader);         //create an indexSearcher for our page
                                                        //NOTE: this operation is slow for large
                                                        //indices (much slower than the search itself)
                                                        //so you might want to keep an IndexSearcher 
                                                        //open
                                                        
        } catch (Exception e) {                         //any error that happens is probably due
                                                        //to a permission problem or non-existant
                                                        //or otherwise corrupt index
%>
                <p>ERROR opening the Index - contact sysadmin!</p>
                <p>Error message: <%=escapeHTML(e.getMessage())%></p>   
<%                error = true;                                  //don't do anything up to the footer
        }

    protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        String queryString = request.getParameter("query");
        int startIndex = 0;
        int maxResults = 10;  // Default to 10 per page

        try {
            startIndex = Integer.parseInt(request.getParameter("startat"));
            maxResults = Integer.parseInt(request.getParameter("maxresults"));
        } catch (Exception ignored) {}

        try {
            IndexSearcher searcher = new IndexSearcher(DirectoryReader.open(FSDirectory.open(Paths.get(INDEX_DIR))));
            Analyzer analyzer = new ThaiAnalyzer();
            Query query = new QueryParser("contents", analyzer).parse(queryString.trim());

            TopDocs hits = searcher.search(query, startIndex + maxResults);
            List<Document> results = new ArrayList<>();
            
            Highlighter highlighter = new Highlighter(
                new SimpleHTMLFormatter("<b class='highlight'>", "</b>"),
                new QueryScorer(query)
            );

            for (int i = startIndex; i < Math.min(hits.scoreDocs.length, startIndex + maxResults); i++) {
                Document doc = searcher.storedFields().document(hits.scoreDocs[i].doc);
                TokenStream tokenStream = analyzer.tokenStream("contents", doc.get("contents"));
                String snippet = highlighter.getBestFragments(tokenStream, doc.get("contents"), 2, "...");

                doc.add(new org.apache.lucene.document.TextField("snippet", snippet, org.apache.lucene.document.Field.Store.YES));
                results.add(doc);
            }

            request.setAttribute("results", results);
            request.setAttribute("totalHits", hits.totalHits.value);
            if (hits.totalHits.value > startIndex + maxResults) {
                request.setAttribute("nextPage", "results.jsp?query=" + queryString + "&startat=" + (startIndex + maxResults) + "&maxresults=" + maxResults);
            }
        } catch (ParseException e) {
            request.setAttribute("error", "Invalid search query.");
        }

        request.getRequestDispatcher("results.jsp").forward(request, response);
    }
}
