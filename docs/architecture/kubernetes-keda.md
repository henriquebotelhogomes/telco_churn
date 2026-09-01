# Kubernetes & KEDA Autoscaling (Fase 2 - Marco M15)

O **Marco M15** implementa a infraestrutura declarativa de orquestração em nuvem com **Kubernetes (K8s)** e dimensionamento elástico híbrido:
1. **Event-Driven Autoscaling (KEDA):** Baseado em *Kafka Consumer Lag* para o processamento de stream.
2. **Resource-Driven Autoscaling (HPA):** Baseado em utilização de CPU e Memória para a API de inferência em alta disponibilidade.

---

## ☸️ Topologia de Produção no Cluster

```mermaid
graph TD
    subgraph Client["Tráfego Externo"]
        EXT_CLI["Clientes B2B / SDK"]
        INGRESS["Ingress Controller (NGINX / SSL)"]
        EXT_CLI --> INGRESS
    end

    subgraph K8sNamespace["Namespace: retainiq-system"]
        SVC["Service: retainiq-api-service:80"]
        INGRESS --> SVC
        
        subgraph APIDeployment["Deployment: retainiq-api (2 a 10 Pods)"]
            POD1["Pod API 1 (CPU / RAM limit)"]
            POD2["Pod API 2 (CPU / RAM limit)"]
            SVC --> POD1
            SVC --> POD2
        end

        subgraph AutoscalingEngines["Motores de Autoscaling"]
            HPA["K8s HPA (CPU > 70% | RAM > 80%)"]
            KEDA["KEDA ScaledObject (Lag > 500 msgs)"]
            HPA -.->|Escala Replicas| APIDeployment
        end

        subgraph StreamDeployment["Deployment: retainiq-stream-worker (1 a 20 Pods)"]
            WORKER1["Stream Worker Pod"]
            KEDA -.->|Escala sob demanda| StreamDeployment
        end
    end

    subgraph Messaging["Kafka Broker (Redpanda)"]
        TOPIC["Tópicos de Telemetria & Billing"]
        TOPIC --> WORKER1
        TOPIC -.->|Métricas de Lag| KEDA
    end
```

---

## 📁 Estrutura de Manifestos Declarativos (`k8s/`)

- 📦 **`namespace.yaml`**: Criação e isolamento do namespace `retainiq-system`.
- ⚙️ **`configmap.yaml` & `secret.yaml`**: Parametrização desacoplada de variáveis de ambiente e chaves.
- 🚀 **`api-deployment.yaml` & `api-service.yaml`**: 2 réplicas mínimas, `podAntiAffinity` entre nós, *readiness* e *liveness probes* em `/health`.
- ⚡ **`stream-consumer-deployment.yaml`**: Processador de streaming Flink desacoplado em background.
- 🌐 **`ingress.yaml`**: Regras de roteamento NGINX e terminação TLS.
- 📈 **`autoscaling/api-hpa.yaml`**: HPA para a API de inferência ($2 \to 10$ réplicas).
- 🎯 **`autoscaling/stream-keda-scaledobject.yaml`**: KEDA `ScaledObject` ($1 \to 20$ réplicas) com gatilho em Kafka Lag $> 500\text{ msgs}$.
