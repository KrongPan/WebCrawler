package org.apache.lucene.demo;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.*;

public class SynonymLoader {
    public static Map<String, String> loadSynonyms(String filePath) throws IOException {
        Map<String, String> synonymMap = new HashMap<>();
        List<String> lines = Files.readAllLines(Paths.get(filePath));

        for (String line : lines) {
            String[] parts = line.split(",\\s*");  // Split on ", " with optional spaces
            if (parts.length == 2) {
                String thai = parts[0].trim();
                String english = parts[1].trim();
                synonymMap.put(english.toLowerCase(), thai);  // English → Thai
            }
        }
        return synonymMap;
    }
}
