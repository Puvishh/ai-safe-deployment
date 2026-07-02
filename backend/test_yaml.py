from app.collectors.kubernetes.yaml_diff import KubernetesYAMLDiff

diff = KubernetesYAMLDiff()

old_file = "../test-repositories/sample_k8/k8s/deployment_old.yaml"
new_file = "../test-repositories/sample_k8/k8s/deployment.yaml"

print("Replica Comparison")
print(diff.compare_replicas(old_file, new_file))

print()

print("Image Comparison")
print(diff.compare_image(old_file, new_file))