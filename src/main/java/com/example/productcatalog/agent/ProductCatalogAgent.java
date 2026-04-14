package com.example.productcatalog.agent;

import com.google.adk.agents.LlmAgent;
import com.google.adk.tools.Annotations.Schema;
import com.google.adk.tools.FunctionTool;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.stream.Collectors;

/** Product catalog LLM agent and {@code getProductInfo} tool (port of {@code product_catalog.py}). */
public final class ProductCatalogAgent {

  private static final Map<String, String> PRODUCT_CATALOG = new LinkedHashMap<>();

  static {
    PRODUCT_CATALOG.put(
        "iphone 15 pro",
        "iPhone 15 Pro, $999, Low Stock (8 units), 128GB, Titanium finish");
    PRODUCT_CATALOG.put(
        "samsung galaxy s24",
        "Samsung Galaxy S24, $799, In Stock (31 units), 256GB, Phantom Black");
    PRODUCT_CATALOG.put(
        "dell xps 15",
        "Dell XPS 15, $1,299, In Stock (45 units), 15.6\" display, 16GB RAM, 512GB SSD");
    PRODUCT_CATALOG.put(
        "macbook pro 14",
        "MacBook Pro 14\", $1,999, In Stock (22 units), M3 Pro chip, 18GB RAM, 512GB SSD");
    PRODUCT_CATALOG.put(
        "sony wh-1000xm5",
        "Sony WH-1000XM5 Headphones, $399, In Stock (67 units), Noise-canceling, 30hr battery");
    PRODUCT_CATALOG.put("ipad air", "iPad Air, $599, In Stock (28 units), 10.9\" display, 64GB");
    PRODUCT_CATALOG.put(
        "lg ultrawide 34",
        "LG UltraWide 34\" Monitor, $499, Out of Stock, Expected: Next week");
  }

  private static final String AGENT_INSTRUCTION =
      """
      You are a product catalog specialist from an external vendor.
      When asked about products, use the get_product_info tool to fetch data from the catalog.
      Provide clear, accurate product information including price, availability, and specs.
      If asked about multiple products, look up each one.
      Be professional and helpful.
      """;

  @Schema(
      description =
          "Look up product information by name (e.g. \"iPhone 15 Pro\", \"MacBook Pro 14\").")
  public static String getProductInfo(
      @Schema(
              name = "product_name",
              description = "Name of the product to look up in the vendor catalog.")
          String productName) {
    String key = productName.toLowerCase(Locale.ROOT).strip();
    if (PRODUCT_CATALOG.containsKey(key)) {
      return "Product: " + PRODUCT_CATALOG.get(key);
    }
    String available =
        PRODUCT_CATALOG.keySet().stream()
            .map(ProductCatalogAgent::pythonStyleTitle)
            .collect(Collectors.joining(", "));
    return "Sorry, I don't have information for "
        + productName
        + ". Available products: "
        + available;
  }

  /** Approximates Python {@code str.title()} for ASCII catalog keys. */
  private static String pythonStyleTitle(String key) {
    StringBuilder sb = new StringBuilder();
    boolean capitalizeNext = true;
    for (int i = 0; i < key.length(); i++) {
      char c = key.charAt(i);
      if (Character.isWhitespace(c)) {
        sb.append(c);
        capitalizeNext = true;
      } else if (capitalizeNext) {
        sb.append(Character.toTitleCase(c));
        capitalizeNext = false;
      } else {
        sb.append(Character.toLowerCase(c));
      }
    }
    return sb.toString();
  }

  public static final LlmAgent ROOT_AGENT =
      LlmAgent.builder()
          .model("gemini-2.5-flash-lite")
          .name("product_catalog_agent")
          .description(
              "External vendor's catalog agent that provides product information and availability")
          .instruction(AGENT_INSTRUCTION)
          .tools(FunctionTool.create(ProductCatalogAgent.class, "getProductInfo"))
          .build();

  private ProductCatalogAgent() {}
}
