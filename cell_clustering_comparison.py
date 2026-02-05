"""
Cell Grouping by Protein Expression - Clustering Method Comparison
==================================================================
This script tests multiple clustering approaches for grouping cells
by their relative fluorescent protein expression levels.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# LOAD DATA
# ============================================================
df = pd.read_csv('/mnt/user-data/uploads/cell_groups.csv')
print("=" * 60)
print("CELL GROUPING ANALYSIS")
print("=" * 60)
print(f"\nDataset: {len(df)} cells")
print(f"Expression range: {df['cell_auc'].min():,} - {df['cell_auc'].max():,}")
print(f"Manual groups: {df['groups'].nunique()} groups")
print(f"\nManual group distribution:")
print(df['groups'].value_counts().sort_index())

# Prepare data
X = df['cell_auc'].values.reshape(-1, 1)
X_scaled = StandardScaler().fit_transform(X)
manual_labels = df['groups'].values
n_clusters = df['groups'].nunique()

# ============================================================
# METHOD 1: K-MEANS CLUSTERING
# ============================================================
print("\n" + "=" * 60)
print("METHOD 1: K-MEANS CLUSTERING")
print("=" * 60)

kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
kmeans_labels = kmeans.fit_predict(X)

# Relabel to match ascending order of cluster centers
order = np.argsort(kmeans.cluster_centers_.flatten())
kmeans_labels_ordered = np.array([np.where(order == l)[0][0] + 1 for l in kmeans_labels])

print(f"Cluster centers (expression values):")
for i, center in enumerate(sorted(kmeans.cluster_centers_.flatten())):
    print(f"  Group {i+1}: {center:,.0f}")

# ============================================================
# METHOD 2: GAUSSIAN MIXTURE MODEL
# ============================================================
print("\n" + "=" * 60)
print("METHOD 2: GAUSSIAN MIXTURE MODEL")
print("=" * 60)

gmm = GaussianMixture(n_components=n_clusters, random_state=42)
gmm_labels = gmm.fit_predict(X)

# Relabel to match ascending order of means
order = np.argsort(gmm.means_.flatten())
gmm_labels_ordered = np.array([np.where(order == l)[0][0] + 1 for l in gmm_labels])

print(f"Component means (expression values):")
for i, (mean, var) in enumerate(sorted(zip(gmm.means_.flatten(), gmm.covariances_.flatten()))):
    print(f"  Group {i+1}: {mean:,.0f} (±{np.sqrt(var):,.0f})")

# ============================================================
# METHOD 3: HIERARCHICAL CLUSTERING
# ============================================================
print("\n" + "=" * 60)
print("METHOD 3: HIERARCHICAL CLUSTERING (Ward)")
print("=" * 60)

# Using Ward's method for linkage
linkage_matrix = linkage(X, method='ward')
hier_labels = fcluster(linkage_matrix, n_clusters, criterion='maxclust')

# Relabel to match ascending order of cluster means
cluster_means = [X[hier_labels == i].mean() for i in range(1, n_clusters + 1)]
order = np.argsort(cluster_means)
hier_labels_ordered = np.array([np.where(order == (l-1))[0][0] + 1 for l in hier_labels])

print(f"Clusters cut at {n_clusters} groups")

# ============================================================
# METHOD 4: JENKS NATURAL BREAKS
# ============================================================
print("\n" + "=" * 60)
print("METHOD 4: JENKS NATURAL BREAKS")
print("=" * 60)

def jenks_breaks(data, n_classes):
    """
    Compute Jenks Natural Breaks for 1D data.
    This method minimizes within-class variance while maximizing between-class variance.
    """
    data = np.sort(data)
    n = len(data)
    
    # Initialize matrices
    lower_class_limits = np.zeros((n + 1, n_classes + 1))
    variance_combinations = np.zeros((n + 1, n_classes + 1))
    variance_combinations[1:, 1:] = np.inf
    lower_class_limits[1, 1] = 1
    
    # Calculate variance combinations
    for l in range(2, n + 1):
        sum_val = 0
        sum_sq = 0
        for m in range(1, l + 1):
            i3 = l - m + 1
            val = data[i3 - 1]
            sum_val += val
            sum_sq += val * val
            variance = sum_sq - (sum_val * sum_val) / m
            
            if i3 > 1:
                for j in range(2, n_classes + 1):
                    if variance_combinations[l, j] >= (variance + variance_combinations[i3 - 1, j - 1]):
                        lower_class_limits[l, j] = i3
                        variance_combinations[l, j] = variance + variance_combinations[i3 - 1, j - 1]
        
        lower_class_limits[l, 1] = 1
        variance_combinations[l, 1] = variance
    
    # Extract breaks
    k = n
    breaks = [data[-1]]
    for j in range(n_classes, 1, -1):
        breaks.insert(0, data[int(lower_class_limits[k, j]) - 2])
        k = int(lower_class_limits[k, j]) - 1
    breaks.insert(0, data[0])
    
    return breaks

# Calculate Jenks breaks
jenks_brks = jenks_breaks(df['cell_auc'].values, n_clusters)
print(f"Natural breaks at: {[f'{b:,.0f}' for b in jenks_brks]}")

# Assign labels based on breaks
jenks_labels = np.digitize(df['cell_auc'].values, jenks_brks[1:-1]) + 1

# ============================================================
# METHOD 5: DBSCAN (Density-Based)
# ============================================================
print("\n" + "=" * 60)
print("METHOD 5: DBSCAN (Density-Based)")
print("=" * 60)

# DBSCAN requires tuning eps parameter
# We'll try to find a good eps that gives similar number of clusters
best_eps = None
best_n_clusters_diff = float('inf')

for eps in np.linspace(0.1, 2.0, 50):
    dbscan = DBSCAN(eps=eps, min_samples=1)
    labels = dbscan.fit_predict(X_scaled)
    n_found = len(set(labels)) - (1 if -1 in labels else 0)
    if abs(n_found - n_clusters) < best_n_clusters_diff:
        best_n_clusters_diff = abs(n_found - n_clusters)
        best_eps = eps

dbscan = DBSCAN(eps=best_eps, min_samples=1)
dbscan_labels = dbscan.fit_predict(X_scaled)
n_dbscan_clusters = len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0)

# Relabel to ascending order
unique_labels = sorted(set(dbscan_labels))
cluster_means = {l: X_scaled[dbscan_labels == l].mean() for l in unique_labels if l != -1}
order = sorted(cluster_means.keys(), key=lambda x: cluster_means[x])
label_map = {old: new + 1 for new, old in enumerate(order)}
label_map[-1] = -1  # Keep noise as -1
dbscan_labels_ordered = np.array([label_map[l] for l in dbscan_labels])

print(f"Best eps: {best_eps:.3f}")
print(f"Found {n_dbscan_clusters} clusters (target: {n_clusters})")

# ============================================================
# COMPARISON METRICS
# ============================================================
print("\n" + "=" * 60)
print("COMPARISON WITH MANUAL GROUPINGS")
print("=" * 60)

methods = {
    'K-Means': kmeans_labels_ordered,
    'GMM': gmm_labels_ordered,
    'Hierarchical': hier_labels_ordered,
    'Jenks': jenks_labels,
    'DBSCAN': dbscan_labels_ordered
}

print(f"\n{'Method':<15} {'ARI':>8} {'NMI':>8} {'Exact Match':>12}")
print("-" * 45)

results = []
for name, labels in methods.items():
    ari = adjusted_rand_score(manual_labels, labels)
    nmi = normalized_mutual_info_score(manual_labels, labels)
    exact = np.mean(manual_labels == labels) * 100
    results.append({'Method': name, 'ARI': ari, 'NMI': nmi, 'Exact': exact})
    print(f"{name:<15} {ari:>8.3f} {nmi:>8.3f} {exact:>11.1f}%")

print("\nMetric interpretation:")
print("  ARI (Adjusted Rand Index): 1.0 = perfect match, 0 = random")
print("  NMI (Normalized Mutual Info): 1.0 = perfect match, 0 = no mutual info")
print("  Exact Match: % of cells assigned to same group as manual")

# ============================================================
# DETAILED COMPARISON TABLE
# ============================================================
print("\n" + "=" * 60)
print("DETAILED CELL-BY-CELL COMPARISON")
print("=" * 60)

comparison_df = df.copy()
comparison_df['Manual'] = manual_labels
comparison_df['K-Means'] = kmeans_labels_ordered
comparison_df['GMM'] = gmm_labels_ordered
comparison_df['Hierarchical'] = hier_labels_ordered
comparison_df['Jenks'] = jenks_labels
comparison_df['DBSCAN'] = dbscan_labels_ordered

# Sort by expression for clarity
comparison_df = comparison_df.sort_values('cell_auc')
print("\nCell assignments (sorted by expression):")
print(comparison_df[['cell_id', 'cell_auc', 'Manual', 'K-Means', 'GMM', 'Hierarchical', 'Jenks']].to_string(index=False))

# ============================================================
# VISUALIZATIONS
# ============================================================
fig, axes = plt.subplots(2, 3, figsize=(14, 9))

# 1. Data distribution with manual groups
ax1 = axes[0, 0]
colors = plt.cm.tab10(np.linspace(0, 1, n_clusters))
for g in range(1, n_clusters + 1):
    mask = manual_labels == g
    ax1.scatter(df.loc[mask, 'cell_auc'], [g] * mask.sum(), 
                c=[colors[g-1]], s=100, alpha=0.7, edgecolors='black', linewidth=0.5)
ax1.set_xlabel('Expression (RawIntDen)')
ax1.set_ylabel('Group')
ax1.set_title('Manual Groupings')
ax1.set_yticks(range(1, n_clusters + 1))

# 2-6. Method comparisons
method_names = ['K-Means', 'GMM', 'Hierarchical', 'Jenks', 'DBSCAN']
method_labels = [kmeans_labels_ordered, gmm_labels_ordered, hier_labels_ordered, 
                 jenks_labels, dbscan_labels_ordered]

for idx, (name, labels) in enumerate(zip(method_names, method_labels)):
    ax = axes.flatten()[idx + 1]
    for g in sorted(set(labels)):
        if g == -1:
            continue
        mask = labels == g
        ax.scatter(df.loc[mask, 'cell_auc'], labels[mask], 
                   c=[colors[g-1] if g <= len(colors) else 'gray'], 
                   s=100, alpha=0.7, edgecolors='black', linewidth=0.5)
    
    ari = adjusted_rand_score(manual_labels, labels)
    ax.set_xlabel('Expression (RawIntDen)')
    ax.set_ylabel('Group')
    ax.set_title(f'{name} (ARI: {ari:.3f})')
    ax.set_yticks(range(1, max(labels) + 1))

plt.tight_layout()
plt.savefig('/home/claude/clustering_comparison.png', dpi=150, bbox_inches='tight')
print("\n✓ Saved comparison plot to clustering_comparison.png")

# Dendrogram for hierarchical clustering
fig2, ax2 = plt.subplots(figsize=(12, 6))
dendrogram(linkage_matrix, labels=df['cell_id'].values, leaf_rotation=90)
ax2.set_title('Hierarchical Clustering Dendrogram')
ax2.set_xlabel('Cell ID')
ax2.set_ylabel('Distance')
plt.tight_layout()
plt.savefig('/home/claude/dendrogram.png', dpi=150, bbox_inches='tight')
print("✓ Saved dendrogram to dendrogram.png")

# Expression distribution histogram with group boundaries
fig3, ax3 = plt.subplots(figsize=(12, 5))
ax3.hist(df['cell_auc'], bins=30, alpha=0.7, color='steelblue', edgecolor='black')
# Add Jenks break lines
for brk in jenks_brks[1:-1]:
    ax3.axvline(brk, color='red', linestyle='--', linewidth=2, alpha=0.7)
ax3.set_xlabel('Expression (RawIntDen)')
ax3.set_ylabel('Count')
ax3.set_title('Expression Distribution with Jenks Natural Breaks (red lines)')
plt.tight_layout()
plt.savefig('/home/claude/expression_distribution.png', dpi=150, bbox_inches='tight')
print("✓ Saved expression distribution to expression_distribution.png")

# ============================================================
# RECOMMENDATIONS
# ============================================================
print("\n" + "=" * 60)
print("RECOMMENDATIONS")
print("=" * 60)

best_method = max(results, key=lambda x: x['ARI'])
print(f"\n★ Best performing method: {best_method['Method']}")
print(f"  - Adjusted Rand Index: {best_method['ARI']:.3f}")
print(f"  - Exact match rate: {best_method['Exact']:.1f}%")

print("\nMethod recommendations by use case:")
print("  • Known number of groups → K-Means or Hierarchical")
print("  • Finding natural breaks → Jenks Natural Breaks")
print("  • Uncertain group boundaries → Gaussian Mixture Model")
print("  • Detecting outliers → DBSCAN")

# Save results
comparison_df.to_csv('/home/claude/clustering_results.csv', index=False)
print("\n✓ Saved full results to clustering_results.csv")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
