<!--
    Licensed to the Apache Software Foundation (ASF) under one or more
    contributor license agreements.  See the NOTICE file distributed with
    this work for additional information regarding copyright ownership.
    The ASF licenses this file to You under the Apache License, Version 2.0
    the "License"); you may not use this file except in compliance with
    the License.  You may obtain a copy of the License at
 
        http://www.apache.org/licenses/LICENSE-2.0
 
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
 -->
<%@page pageEncoding="UTF-8"%>
<%@ page import = "java.util.stream.Collectors, java.util.HashMap, org.apache.lucene.index.IndexableField, java.util.Map, javax.servlet.*, javax.servlet.http.*, java.io.*, java.net.URLEncoder, java.net.URLDecoder, java.nio.file.Paths, org.apache.lucene.analysis.Analyzer, org.apache.lucene.analysis.TokenStream, org.apache.lucene.analysis.standard.StandardAnalyzer, org.apache.lucene.analysis.th.ThaiAnalyzer, org.apache.lucene.document.Document, org.apache.lucene.index.DirectoryReader, org.apache.lucene.index.IndexReader, org.apache.lucene.queryparser.classic.QueryParser, org.apache.lucene.queryparser.classic.ParseException, org.apache.lucene.search.IndexSearcher, org.apache.lucene.search.Query, org.apache.lucene.search.ScoreDoc, org.apache.lucene.search.TopDocs, org.apache.lucene.search.highlight.Highlighter, org.apache.lucene.search.highlight.InvalidTokenOffsetsException, org.apache.lucene.search.highlight.QueryScorer, org.apache.lucene.search.highlight.SimpleHTMLFormatter, org.apache.lucene.search.highlight.SimpleFragmenter, org.apache.lucene.store.FSDirectory, java.net.URL" %>
<%@ page import="org.apache.lucene.demo.SynonymExpander" %>
<%@ page import="org.apache.lucene.demo.SynonymLoader" %>
<%
/*
        Author: Andrew C. Oliver, SuperLink Software, Inc. (acoliver2@users.sourceforge.net)

        This jsp page is deliberatly written in the horrible java directly embedded 
        in the page style for an easy and concise demonstration of Lucene.
        Due note...if you write pages that look like this...sooner or later
        you'll have a maintenance nightmare.  If you use jsps...use taglibs
        and beans!  That being said, this should be acceptable for a small
        page demonstrating how one uses Lucene in a web app. 

        This is also deliberately overcommented. ;-)

*/
%>
<%!
public String escapeHTML(String s) {
  s = s.replaceAll("&", "&amp;");
  s = s.replaceAll("<", "&lt;");
  s = s.replaceAll(">", "&gt;");
  s = s.replaceAll("\"", "&quot;");
  s = s.replaceAll("'", "&apos;");
  return s;
}
%>
<%@include file="header.jsp"%>

<head>
    <title><%= appTitle %></title>
    <style>
        body {
    font-family: Arial, sans-serif;
    background-color: #f4f4f4;
    margin: 0;
    padding: 0;
}

.container {
    width: 80%;
    margin: 0 auto;
    padding: 20px;
    background-color: white;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

h1 {
    text-align: center;
    font-size: 2em;
    margin-bottom: 20px;
}

p {
    font-size: 1em;
    color: #333;
}

.button {
            background-color: #4CAF50; /* Green background */
            color: white; /* White text */
            padding: 10px 20px; /* Padding around the text */
            text-align: center; /* Center text */
            text-decoration: none; /* Remove underline */
            display: inline-block; /* Make it inline like a button */
            font-size: 16px; /* Font size */
            cursor: pointer;
            border-radius: 5px; 
            transition: background-color 0.3s;
        }

        /* Button hover effect */
        .button:hover {
            background-color: #45a049; /* Darker green when hovered */
        }

table {
    width: 100%;
    margin-top: 20px;
    border-collapse: collapse;
}

table td {
    padding: 10px;
    border-bottom: 1px solid #eee;
}

table a {
    color: #0066cc;
    text-decoration: none;
}

table a:hover {
    text-decoration: underline;
}

.highlight {
    background-color: yellow;
    font-weight: bold;
}

footer {
    text-align: center;
    margin-top: 40px;
    font-size: 0.9em;
    color: #666;
}

/* Form styling */
        form {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-top: 30px;
        }

        form input[type="text"], form input[type="number"] {
            padding: 10px;
            width: 80%;
            margin: 10px 0;
            border: 1px solid #ccc;
            border-radius: 5px;
            font-size: 16px;
        }

        form input[type="submit"] {
            background-color: #1a73e8;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 15px;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s;
        }

    </style>
</head>
<p class="button" onclick="window.location.href='/Web-ir_project_web/'">Go to Homepage</p>
<form name="search" action="results.jsp" method="get">
            <p>
                <input id="searchInput" name="query" type="text" placeholder="Enter place name or keyword" required />
                <script>
				  // Function to get URL parameters
				  function getQueryParam(param) {
				    const urlParams = new URLSearchParams(window.location.search);
				    return urlParams.get(param);
				  }
				
				  // Set the input value if the "query" parameter exists
				  const queryValue = getQueryParam("query");
				  if (queryValue) {
				    document.getElementById("searchInput").value = queryValue;
				  }
				</script>
            </p>
            <p>
                <input name="maxresults" type="number" value="10" /> Results Per Page
            </p>
            <p>
                <input type="submit" value="Search" />
            </p>
</form>
<%
        boolean error = false;                  //used to control flow for error messages
        String indexName = indexLocation;       //local copy of the configuration variable
        IndexSearcher searcher = null;          //the searcher used to open/search the index
        Query query = null;                     //the Query created by the QueryParser
        TopDocs hits = null;                    //the search results
        int numTotalHits = 0;                   //the number of search results
        int startindex = 0;                     //the first index displayed on this page
        int maxpage    = 50;                    //the maximum items displayed on this page
        String queryString = null;              //the query entered in the previous page
        String startVal    = null;              //string version of startindex
        String maxresults  = null;              //string version of maxpage
        int thispage = 0;                       //used for the for/next either maxpage or
                                                //hits.totalHits - startindex - whichever is
                                                //less

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
%>
<%
       //Analyzer analyzer = new StandardAnalyzer(Version.LUCENE_CURRENT);           //construct our usual analyzer
        Map<String, String> synonymMap = SynonymLoader.loadSynonyms();
    	Analyzer analyzer = new ThaiAnalyzer();
    	SynonymExpander expander = new SynonymExpander(synonymMap, analyzer);

       if (error == false) {                                           //did we open the index?
                //queryString = URLDecoder.decode(request.getParameter("query"),"UTF-8");           //get the search criteria
                queryString = request.getParameter("query");           //get the search criteria
                startVal    = request.getParameter("startat");         //get the start index
                maxresults  = request.getParameter("maxresults");      //get max results per page
                try {
                        maxpage    = Integer.parseInt(maxresults);    //parse the max results first
                        startindex = Integer.parseInt(startVal);      //then the start index  
                } catch (Exception e) { } //we don't care if something happens we'll just start at 0
                                          //or end at 50
                

                if (queryString == null)
                        throw new ServletException("no query "+       //if you don't have a query then
                                                   "specified");      //you probably played on the 
                                                                      //query string so you get the 
                                                                      //treatment

//                Analyzer analyzer = new ThaiAnalyzer();
                try {
                        QueryParser qp = new QueryParser("contents", analyzer);
                        String expandedQuery = expander.expandQuery(queryString.trim());
                        query = qp.parse(expandedQuery);
                } catch (ParseException e) {                          //query and construct the Query
                                                                      //object
                                                                      //if it's just "operator error"
                                                                      //send them a nice error HTML
                                                                      
%>
                        <p>Error while parsing query: <%=escapeHTML(e.getMessage())%></p>
<%
                        error = true;                                 //don't bother with the rest of
                                                                      //the page
                }
        }
%>
<%
        if (error == false && searcher != null) {                     // if we've had no errors
                                                                      // searcher != null was to handle
                                                                      // a weird compilation bug 
                thispage = maxpage;                                   // default last element to maxpage
                hits = searcher.search(query, maxpage + startindex);  // run the query
                numTotalHits = Math.toIntExact(hits.totalHits.value());
                if (numTotalHits == 0) {                             // if we got no results tell the user
%>
                <p> I'm sorry I couldn't find what you were looking for. </p>
<%
                error = true;                                        // don't bother with the rest of the
                                                                     // page
                }
        }

        if (error == false && searcher != null) {                   
			out.println("<div class='container'>");
	        out.println("<h2>Search Results</h2>");
	        out.println("<table>");
	        
	        QueryScorer queryScorer = new QueryScorer(query);
	        SimpleHTMLFormatter yellow_highlight = new SimpleHTMLFormatter("<span class='highlight'>", "</span>");
	        Highlighter highlighter = new Highlighter(yellow_highlight, queryScorer);
	        
	        for (int i = startindex; i < (thispage + startindex); i++) {
	            Document doc = searcher.storedFields().document(hits.scoreDocs[i].doc);
	            String doctitle = doc.get("title");
	            String url = doc.get("path");
	
	            if (url != null && url.startsWith("../webapps/")) {
	                url = url.substring(10);
	            }
	            if ((doctitle == null) || doctitle.equals("")) doctitle = url;
	
	            out.println("<tr><td><b>" + (i + 1) + "</b></td><td><b>" + doctitle + "</b></td></tr>");
	            out.println("<tr><td></td><td>");
	            
	            Map<String, Integer> provinces = new HashMap<>();

	            // If provinces were stored as separate fields like "province_provinceName", you could fetch them like this
	            for (IndexableField field : doc.getFields()) {
	              if (field.name().startsWith("province_")) {
	            	  provinces.put(field.name().split("province_")[1], Integer.parseInt(field.stringValue()));
	              }
	            }
	            
	            String result = provinces.entrySet().stream()
	                      .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())  // Sort by Integer value
	                      .map(entry -> entry.getKey())  // Format each entry as "ProvinceNumber"
	                      .collect(Collectors.joining(", "));  // Join with ", "

	              out.println("<tr><td></td><td>" + "Provinces: " + result + "</td></tr>");
		            out.println("<tr><td></td><td>");
	
	            String content = doc.get("contents");
	            TokenStream tokenStream = analyzer.tokenStream("contents", content);
	            highlighter.setTextFragmenter(new SimpleFragmenter(100));
	
	            try {
	                String fragment = highlighter.getBestFragments(tokenStream, content, 2, "...");
	                out.println(fragment);
	            } catch (InvalidTokenOffsetsException e) {
	                e.printStackTrace();
	            }
	
	            out.println("</td></tr>");

	            String fullUrl = doc.get("url").replace("dummy", ""); // Get the full URL

	            try {
	                // Check if fullUrl contains "http://" or "https://" properly
	                if (!fullUrl.startsWith("http://") && !fullUrl.startsWith("https://")) {
	                    fullUrl = "http://" + fullUrl; // Add http:// if missing
	                }

	                URL parsedUrl = new URL(fullUrl); // Parse the URL
	                String host = parsedUrl.getHost(); // Extract domain (may be incorrect if URL is malformed)
	                String path = parsedUrl.getPath(); // Extract path

	                // Remove leading slash from path if exists
	                if (path.startsWith("/")) {
	                    path = path.substring(1);
	                }

	                String cleanedUrl;
	                
	                // If the host is incorrect (like "trueID"), try fixing it by extracting the correct domain from fullUrl
	                if (!host.contains(".")) {
	                	cleanedUrl = path;
	                } else {
	                	cleanedUrl = host + "/" + path;
	                }

	                // Output results
	                out.println("<tr><td></td><td><a href='https://" + cleanedUrl + "' target='_blank'>" + cleanedUrl + "</a></td></tr>");

	            } catch (Exception e) {
	                out.println("<tr><td>Error:</td><td>Invalid URL format</td></tr>");
	            }


	            out.println("<tr><td></td><td></td></tr>");
	        }

	        // Pagination Links
	        int totalPages = (int) Math.ceil((double) numTotalHits / maxpage);
	        int currentPage = (startindex / maxpage) + 1;

	        out.println("<tr><td colspan='2' style='text-align: center;'>");

	        // **Previous Page Link** (Moves 1 page back)
	        if (currentPage > 1) {
	            int prevPageStart = (currentPage - 2) * maxpage;
	            out.println("<a href='results.jsp?query=" + URLEncoder.encode(queryString) + "&amp;maxresults=" + maxpage + "&amp;startat=" + prevPageStart + "'>&laquo; Prev</a>&nbsp;&nbsp;");
	        }

	        // **Determine the range of pages to display (max 10 pages at a time)**
	        int pagesPerRange = 10;
	        int startPage = ((currentPage - 1) / pagesPerRange) * pagesPerRange + 1;
	        int endPage = Math.min(startPage + pagesPerRange - 1, totalPages);

	        // **Previous Range Link** (Moves 10 pages back)
	        if (startPage > 1) {
	            int prevRangeStart = (startPage - 2) * maxpage;
	            out.println("<a href='results.jsp?query=" + URLEncoder.encode(queryString) + "&amp;maxresults=" + maxpage + "&amp;startat=" + prevRangeStart + "'>...</a>&nbsp;&nbsp;");
	        }

	        // **Display numbered page links**
	        for (int pageNum = startPage; pageNum <= endPage; pageNum++) {
	            int pageStartIndex = (pageNum - 1) * maxpage;
	            if (pageNum == currentPage) {
	                out.println("<b>" + pageNum + "</b>&nbsp;&nbsp;");
	            } else {
	                out.println("<a href='results.jsp?query=" + URLEncoder.encode(queryString) + "&amp;maxresults=" + maxpage + "&amp;startat=" + pageStartIndex + "'>" + pageNum + "</a>&nbsp;&nbsp;");
	            }
	        }

	        // **Next Range Link** (Moves 10 pages forward)
	        if (endPage < totalPages) {
	            int nextRangeStart = endPage * maxpage;
	            out.println("&nbsp;&nbsp;<a href='results.jsp?query=" + URLEncoder.encode(queryString) + "&amp;maxresults=" + maxpage + "&amp;startat=" + nextRangeStart + "'>...</a>");
	        }

	        // **Next Page Link** (Moves 1 page forward)
	        if (currentPage < totalPages) {
	            int nextPageStart = (currentPage) * maxpage;
	            out.println("&nbsp;&nbsp;<a href='results.jsp?query=" + URLEncoder.encode(queryString) + "&amp;maxresults=" + maxpage + "&amp;startat=" + nextPageStart + "'>Next &raquo;</a>");
	        }


	        out.println("</td></tr>");
	        
	        out.println("</table>");
	        out.println("</div>");
	
	      }                                    //then include our footer.
         //if (searcher != null)
         //       searcher.close();
%>
