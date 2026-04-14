# Product catalog A2A agent (Java)

This project is a **Maven** application that exposes the Google **Agent Development Kit (ADK)** product-catalog agent over the **Agent2Agent (A2A)** protocol using **Quarkus**. The in-memory catalog and behavior mirror `[product_catalog.py](product_catalog.py)`.

---

## 1. Prerequisites

1. **JDK 17** (or newer LTS). Verify with `java -version`.
2. **Apache Maven 3.8.6 or newer** (Quarkus 3.30 requires this; Maven 3.9.x is recommended). Verify with `mvn -version`.
3. A **Gemini API key** from [Google AI Studio](https://aistudio.google.com/app/apikey) (used as `GOOGLE_API_KEY` at runtime).

---

## 2. Maven dependencies — optional; only when needed

**Downloading or updating dependencies is not something you do on every run of the finished application.** It happens only when **Maven** runs and decides something is missing or must be refreshed.

Maven will hit the network (or use your local cache) when you run goals such as `compile`, `package`, or `quarkus:dev`, **only if** for example:

- This is the **first** build on a machine or in a clean environment.
- You changed `**pom.xml`** or dependency versions.
- You used `**mvn clean**` and artifacts were removed from `target/` (Maven may still use `~/.m2` without re-downloading).
- You passed `**-U**` / **--update-snapshots** and Maven checks for newer releases.
- Part of the cache under `**~/.m2/repository`** (or your project-local repo) was deleted.

After dependencies are present in the local repository, many builds are **fully offline** aside from compiling your sources.

**Optional — enforce offline mode** (fails fast if something is missing from the cache):

```bash
mvn -o clean package -DskipTests
```

**Running the packaged app with `java -jar`** does **not** invoke Maven and does **not** download Maven dependencies.

---

## 3. Build this project

Work from the repository root (the directory that contains this `pom.xml`).

### Maven Central vs local repository

- **Remote artifacts** almost always come from **Maven Central** (`https://repo.maven.apache.org/maven2/`) and any extra repositories defined in your `~/.m2/settings.xml` or this `pom.xml`. That does not change between the two options below.
- **Local repository** means the **on-disk cache** where Maven stores downloaded JARs and POMs. You either use the default under your home directory, or you point Maven at a folder **inside this project** with `-Dmaven.repo.local=...`.

### Option A — build using the default local repository (`~/.m2/repository`)

Omit `-Dmaven.repo.local`. Maven caches dependencies under your user home (typically `**~/.m2/repository`**). This is the usual choice on a developer machine.

```bashr
cd /path/to/agent2agent

mvn clean compile

mvn clean package -DskipTests
```

### Option B — build using a project-local repository (`./.m2/repository`)

Pass `**-Dmaven.repo.local="${PWD}/.m2/repository"**` so the cache lives **inside the clone** (for example in CI, restricted environments, or when you want all build artifacts for this tree in one place). The folder is gitignored (see `[.gitignore](.gitignore)`).

```bash
cd /path/to/agent2agent

mvn clean compile -Dmaven.repo.local="${PWD}/.m2/repository"

mvn clean package -DskipTests -Dmaven.repo.local="${PWD}/.m2/repository"
```

On success, compiled output appears under `**target/**`. The runnable **Quarkus application bundle** is under `**target/quarkus-app/`** after `package` (see [section 4](#4-package-the-application-as-a-runnable-bundle-jar)).

**IDE (optional):** open the folder as a **Maven** project so the IDE uses this `pom.xml` and JDK 17.

If dependency downloads fail with TLS or corporate proxy errors, fix JVM trust store / proxy settings for Maven (same as any other Maven project on your network).

---

## 4. Package the application as a runnable bundle (JAR)

Quarkus packages a **directory** named `**target/quarkus-app/`** (not a single “fat” JAR by default). The entry point is `**quarkus-run.jar**`; it expects the `**lib/**` tree and other files **next to it** inside that folder.

1. Ensure you have already resolved dependencies at least once (see [section 2](#2-maven-dependencies--optional-only-when-needed)).
2. From the repository root, produce the bundle:
  **Option A (default `~/.m2/repository`):**
   **Option B (project-local repository):**
3. Confirm the layout (you should see `**quarkus-run.jar`** and `**lib/**` among others):
  ```bash
   ls target/quarkus-app/
  ```

To deploy elsewhere, copy the **entire** `**target/quarkus-app/`** directory (preserve its internal structure). You only need a **JRE/JDK 17+** on the target host to run it—**Maven is not required** on that host to start the server.

---

## 5. Run the A2A `product_catalog` agent

The agent listens on **port 8001** by default (see `[src/main/resources/application.properties](src/main/resources/application.properties)`).

### 5.1 Set the API key

In the same shell where you start the server:

```bash
export GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
```

(On Windows CMD, use `set GOOGLE_API_KEY=...`; in PowerShell, `$env:GOOGLE_API_KEY="..."`.)

### 5.2 Option A — development mode (Maven; may resolve dependencies if needed)

From the repository root:

```bash
mvn quarkus:dev
```

If you built with **project-local** `maven.repo.local` ([section 3, Option B](#option-b--build-using-a-project-local-repository-m2repository)), use the same flag so Maven uses that cache:

```bash
mvn quarkus:dev -Dmaven.repo.local="${PWD}/.m2/repository"
```

Wait until the log shows Quarkus **listening on** `http://localhost:8001` (or `0.0.0.0:8001`). Leave this process running.

`quarkus:dev` is intended for **local development** (live reload, dev tooling). It **does** start the JVM through Maven, so Maven *may* contact remote repositories when something is out of date (see [section 2](#2-maven-dependencies--optional-only-when-needed)).

### 5.3 Option B — run the packaged application with `java` (no Maven)

Use this after a successful `**mvn package`** ([section 4](#4-package-the-application-as-a-runnable-bundle-jar)). **No dependency download** occurs at startup—only the JVM runs.

From the repository root:

```bash
cd /path/to/agent2agent
export GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
java -jar target/quarkus-app/quarkus-run.jar
```

If you copied `**quarkus-app/**` to another machine or folder, `cd` into that directory and run:

```bash
export GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
java -jar quarkus-run.jar
```

Optional: override the HTTP port for this launch only:

```bash
java -Dquarkus.http.port=8001 -jar target/quarkus-app/quarkus-run.jar
```

### 5.4 Verify the server

- **Agent card (discovery):**  
`GET` [http://localhost:8001/.well-known/agent-card.json](http://localhost:8001/.well-known/agent-card.json)
  Example:
  ```bash
  curl -fsS "http://localhost:8001/.well-known/agent-card.json"
  ```
- **A2A JSON-RPC (invoke the agent):** send a `POST` to the **server root** with `Content-Type: application/json` and a JSON-RPC body whose method is `**message/send`**, as in the [ADK Java A2A exposing quickstart](https://google.github.io/adk-docs/a2a/quickstart-exposing-java/).
  Example:
  ```bash
  curl -fsS -X POST "http://localhost:8001/" \
    -H "Content-Type: application/json" \
    -d '{
      "jsonrpc": "2.0",
      "id": "cli-check",
      "method": "message/send",
      "params": {
        "message": {
          "kind": "message",
          "contextId": "cli-demo-context",
          "messageId": "cli-check-id",
          "role": "user",
          "parts": [
            { "kind": "text", "text": "What is the price of the iPhone 15 Pro?" }
          ]
        }
      }
    }'
  ```

The running agent is the `**product_catalog_agent**` defined in `[ProductCatalogAgent.java](src/main/java/com/example/productcatalog/agent/ProductCatalogAgent.java)`; it uses the `**getProductInfo**` tool against the in-memory catalog.

### 5.5 Stop the server

Press **Ctrl+C** in the terminal where the process is running. If port 8001 is still held by a stray process, free it (e.g. `fuser -k 8001/tcp` on Linux) before starting again.

---

## Quick reference


| Item              | Value                                                     |
| ----------------- | --------------------------------------------------------- |
| Default HTTP port | `8001`                                                    |
| Agent card URL    | `http://localhost:8001/.well-known/agent-card.json`       |
| JSON-RPC URL      | `http://localhost:8001/` (POST, `message/send`)           |
| Required env      | `GOOGLE_API_KEY`                                          |
| Packaged bundle   | `target/quarkus-app/` (run `java -jar …/quarkus-run.jar`) |
| Dev entrypoint    | `mvn quarkus:dev`                                         |


