from app.collectors.kubernetes.analyzer import KubernetesAnalyzer

analyzer = KubernetesAnalyzer()

result = analyzer.analyze(
    "../test-repositories/sample_k8/k8s/deployment_old.yaml",
    "../test-repositories/sample_k8/k8s/deployment.yaml"
)

print(result)