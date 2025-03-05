package org.apache.lucene.demo;

import org.apache.lucene.analysis.Analyzer;

import java.util.Map;

public class SynonymExpander {
    private final Map<String, String> synonymMap;
    private final Analyzer analyzer;

    public SynonymExpander(Map<String, String> synonymMap, Analyzer analyzer) {
        this.synonymMap = synonymMap;
        this.analyzer = analyzer;
    }

    // Expanding query by adding synonyms
    public String expandQuery(String userQuery) {
        StringBuilder expandedQuery = new StringBuilder();

        String[] words = userQuery.split("\\s+"); // Split query into words
        for (String word : words) {
            String lowerWord = word.toLowerCase();

            if (synonymMap.containsKey(lowerWord)) {
                // If synonym exists, add both the original and synonym to the query
                expandedQuery.append(synonymMap.get(lowerWord)).append(" OR ");
            }

            // Always include the original word
            expandedQuery.append(word).append(" OR ");
        }

        // Remove last " OR "
        return expandedQuery.substring(0, expandedQuery.length() - 4);
    }
}
