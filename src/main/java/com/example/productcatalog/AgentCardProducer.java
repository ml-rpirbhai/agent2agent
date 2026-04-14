package com.example.productcatalog;

import io.a2a.server.PublicAgentCard;
import io.a2a.spec.AgentCard;
import io.a2a.util.Utils;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.inject.Produces;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/** Loads the public {@link AgentCard} from classpath JSON. */
@ApplicationScoped
public class AgentCardProducer {

  @Produces
  @PublicAgentCard
  public AgentCard agentCard() {
    try (InputStream is = getClass().getResourceAsStream("/agent/agent.json")) {
      if (is == null) {
        throw new RuntimeException("agent/agent.json not found on classpath");
      }
      String json = new String(is.readAllBytes(), StandardCharsets.UTF_8);
      return Utils.OBJECT_MAPPER.readValue(json, AgentCard.class);
    } catch (Exception e) {
      throw new RuntimeException("Failed to load AgentCard from JSON", e);
    }
  }
}
