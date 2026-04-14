package com.example.productcatalog;

import com.example.productcatalog.agent.ProductCatalogAgent;
import com.google.adk.a2a.executor.AgentExecutorConfig;
import com.google.adk.artifacts.InMemoryArtifactService;
import com.google.adk.sessions.InMemorySessionService;
import io.a2a.server.agentexecution.AgentExecutor;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.inject.Produces;
import org.eclipse.microprofile.config.inject.ConfigProperty;

/** Produces the {@link AgentExecutor} that runs the product catalog agent over A2A. */
@ApplicationScoped
public class AgentExecutorProducer {

  @ConfigProperty(name = "my.adk.app.name", defaultValue = "product-catalog")
  String appName;

  @Produces
  public AgentExecutor agentExecutor() {
    return new com.google.adk.a2a.executor.AgentExecutor.Builder()
        .agent(ProductCatalogAgent.ROOT_AGENT)
        .appName(appName)
        .sessionService(new InMemorySessionService())
        .artifactService(new InMemoryArtifactService())
        .agentExecutorConfig(AgentExecutorConfig.builder().build())
        .build();
  }
}
