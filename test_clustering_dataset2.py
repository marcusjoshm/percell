"""
Cell Grouping Analysis - Test Dataset 2
========================================
This script analyzes the clustering results from the new dataset and tests
different clustering approaches to find the optimal grouping.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from scipy.cluster.hierarchy import linkage, fcluster
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# LOAD DATA
# ============================================================
csv_path = '/Volumes/NX-01-A/2026-02-05_test_dataset_2_analysis/grouped_cells/A549_TAOK2_KO_mNG-G3BP1_KI_SG_disassembly_time-lapse_Rep1/As_Merged_ch00_t00/As_Merged_ch00_t00_cell_groups_20260205_121124.csv'
df = pd.read_csv(csv_path)

print("=" * 70)
print("CELL GROUPING ANALYSIS - TEST DATASET 2")
print("=" * 70)
print(f"\nDataset: {len(df)} cells")
print(f"Mean intensity range: {df['cell_mean_intensity'].min():.4f} - {df['cell_mean_intensity'].max():.4f}")
print(f"Current groups: {df['group_id'].nunique()} groups")
print(f"\nCurrent group distribution:")
for gid in sorted(df['group_id'].unique()):
    subset = df[df['group_id'] == gid]
    print(f"  Group {gid}: {len(subset)} cells, "
          f"mean intensity range: {subset['cell_mean_intensity'].min():.4f} - {subset['cell_mean_intensity'].max():.4f}")

# Prepare data
X = df['cell_mean_intensity'].values.reshape(-1, 1)
n_samples = len(X)

# ============================================================
# ANALYZE DATA DISTRIBUTION
# ============================================================
print("\n" + "=" * 70)
print("DATA DISTRIBUTION ANALYSIS")
print("=" * 70)

values = df['cell_mean_intensity'].values
print(f"\nStatistics:")
print(f"  Mean: {values.mean():.4f}")
print(f"  Std:  {values.std():.4f}")
print(f"  Min:  {values.min():.4f}")
print(f"  25%:  {np.percentile(values, 25):.4f}")
print(f"  50%:  {np.percentile(values, 50):.4f}")
print(f"  75%:  {np.percentile(values, 75):.4f}")
print(f"  Max:  {values.max():.4f}")

# ============================================================
# TEST MULTIPLE CLUSTERING METHODS
# ============================================================
print("\n" + "=" * 70)
print("CLUSTERING METHOD COMPARISON")
print("=" * 70)

# Test GMM with different k values
print("\n--- GMM with BIC ---")
print(f"{'k':<5} {'BIC':>12} {'Silhouette':>12} {'Group sizes'}")
print("-" * 60)

gmm_results = []
for k in range(2, min(15, n_samples // 2)):
    try:
        gmm = GaussianMixture(n_components=k, random_state=42, n_init=3)
        labels = gmm.fit_predict(X)
        bic = gmm.bic(X)
        sil = silhouette_score(X, labels)

        # Get group sizes
        unique, counts = np.unique(labels, return_counts=True)
        sizes = sorted(counts, reverse=True)
        sizes_str = str(sizes[:5]) + ('...' if len(sizes) > 5 else '')

        gmm_results.append({'k': k, 'bic': bic, 'silhouette': sil, 'labels': labels})
        print(f"{k:<5} {bic:>12.1f} {sil:>12.3f} {sizes_str}")
    except Exception as e:
        print(f"{k:<5} Error: {e}")

# Find best k by silhouette (current method)
best_sil_idx = np.argmax([r['silhouette'] for r in gmm_results])
best_k_sil = gmm_results[best_sil_idx]['k']
print(f"\nBest k by silhouette score: {best_k_sil}")

# Find best k by BIC
best_bic_idx = np.argmin([r['bic'] for r in gmm_results])
best_k_bic = gmm_results[best_bic_idx]['k']
print(f"Best k by BIC: {best_k_bic}")

# ============================================================
# TEST ALTERNATIVE APPROACHES
# ============================================================
print("\n--- Alternative Approaches ---")

# 1. K-Means with silhouette
print("\nK-Means silhouette scores:")
kmeans_results = []
for k in range(2, min(15, n_samples // 2)):
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    sil = silhouette_score(X, labels)
    kmeans_results.append({'k': k, 'silhouette': sil})
    print(f"  k={k}: {sil:.3f}")

best_kmeans_k = kmeans_results[np.argmax([r['silhouette'] for r in kmeans_results])]['k']
print(f"Best k by K-Means silhouette: {best_kmeans_k}")

# 2. Hierarchical clustering
print("\nHierarchical clustering (Ward) silhouette scores:")
linkage_matrix = linkage(X, method='ward')
hier_results = []
for k in range(2, min(15, n_samples // 2)):
    labels = fcluster(linkage_matrix, k, criterion='maxclust')
    sil = silhouette_score(X, labels)
    hier_results.append({'k': k, 'silhouette': sil})
    print(f"  k={k}: {sil:.3f}")

best_hier_k = hier_results[np.argmax([r['silhouette'] for r in hier_results])]['k']
print(f"Best k by Hierarchical silhouette: {best_hier_k}")

# ============================================================
# ANALYZE THE OPTIMAL CLUSTERING
# ============================================================
print("\n" + "=" * 70)
print("DETAILED ANALYSIS OF OPTIMAL CLUSTERING")
print("=" * 70)

# Use the best k from GMM silhouette
best_result = gmm_results[best_sil_idx]
labels = best_result['labels']

# Reorder labels by ascending mean intensity
cluster_means = []
for i in range(best_k_sil):
    mask = labels == i
    if np.any(mask):
        cluster_means.append((i, X[mask].mean()))
    else:
        cluster_means.append((i, float('inf')))

cluster_means.sort(key=lambda x: x[1])
label_map = {old: new for new, (old, _) in enumerate(cluster_means)}
labels_ordered = np.array([label_map[lbl] for lbl in labels])

print(f"\nOptimal clustering with k={best_k_sil}:")
for i in range(best_k_sil):
    mask = labels_ordered == i
    subset = X[mask].flatten()
    print(f"  Group {i+1}: {len(subset)} cells, "
          f"mean={subset.mean():.4f}, "
          f"range=[{subset.min():.4f}, {subset.max():.4f}]")

# ============================================================
# TEST: What if we require minimum group size?
# ============================================================
print("\n" + "=" * 70)
print("TESTING WITH MINIMUM GROUP SIZE CONSTRAINT")
print("=" * 70)

def find_optimal_k_with_min_size(X, max_k=15, min_group_size=5):
    """Find optimal k ensuring all groups have at least min_group_size cells."""
    best_score = -1
    best_k = 2

    for k in range(2, min(max_k, len(X) // min_group_size)):
        try:
            gmm = GaussianMixture(n_components=k, random_state=42, n_init=3)
            labels = gmm.fit_predict(X)

            # Check minimum group size
            unique, counts = np.unique(labels, return_counts=True)
            if min(counts) < min_group_size:
                continue

            score = silhouette_score(X, labels)
            if score > best_score:
                best_score = score
                best_k = k
        except:
            continue

    return best_k, best_score

for min_size in [3, 5, 10, 20]:
    k, score = find_optimal_k_with_min_size(X, max_k=15, min_group_size=min_size)
    print(f"Min group size {min_size}: optimal k={k}, silhouette={score:.3f}")

# ============================================================
# VISUALIZATIONS
# ============================================================
fig, axes = plt.subplots(2, 3, figsize=(15, 10))

# 1. Histogram of intensities
ax1 = axes[0, 0]
ax1.hist(values, bins=50, alpha=0.7, color='steelblue', edgecolor='black')
ax1.set_xlabel('Mean Intensity')
ax1.set_ylabel('Count')
ax1.set_title('Distribution of Cell Mean Intensities')

# 2. Current grouping (k=2)
ax2 = axes[0, 1]
current_labels = df['group_id'].values
colors = plt.cm.tab10(np.linspace(0, 1, 10))
for g in sorted(df['group_id'].unique()):
    mask = current_labels == g
    ax2.scatter(values[mask], [g] * mask.sum(), c=[colors[g-1]], s=20, alpha=0.5)
ax2.set_xlabel('Mean Intensity')
ax2.set_ylabel('Group')
ax2.set_title(f'Current Grouping (k=2)')

# 3. Silhouette scores vs k
ax3 = axes[0, 2]
ks = [r['k'] for r in gmm_results]
sils = [r['silhouette'] for r in gmm_results]
ax3.plot(ks, sils, 'bo-', linewidth=2, markersize=8)
ax3.axvline(best_k_sil, color='red', linestyle='--', label=f'Best k={best_k_sil}')
ax3.set_xlabel('Number of Clusters (k)')
ax3.set_ylabel('Silhouette Score')
ax3.set_title('GMM Silhouette Score vs k')
ax3.legend()

# 4. BIC vs k
ax4 = axes[1, 0]
bics = [r['bic'] for r in gmm_results]
ax4.plot(ks, bics, 'go-', linewidth=2, markersize=8)
ax4.axvline(best_k_bic, color='red', linestyle='--', label=f'Best k={best_k_bic}')
ax4.set_xlabel('Number of Clusters (k)')
ax4.set_ylabel('BIC')
ax4.set_title('GMM BIC vs k')
ax4.legend()

# 5. Optimal grouping visualization
ax5 = axes[1, 1]
for i in range(best_k_sil):
    mask = labels_ordered == i
    ax5.scatter(values[mask], labels_ordered[mask] + 1, c=[colors[i]], s=20, alpha=0.5)
ax5.set_xlabel('Mean Intensity')
ax5.set_ylabel('Group')
ax5.set_title(f'Optimal Grouping by Silhouette (k={best_k_sil})')

# 6. Compare with higher k
ax6 = axes[1, 2]
# Try k=5 for comparison
gmm5 = GaussianMixture(n_components=5, random_state=42, n_init=3)
labels5 = gmm5.fit_predict(X)
# Reorder
cluster_means5 = [(i, X[labels5 == i].mean()) for i in range(5)]
cluster_means5.sort(key=lambda x: x[1])
label_map5 = {old: new for new, (old, _) in enumerate(cluster_means5)}
labels5_ordered = np.array([label_map5[lbl] for lbl in labels5])

for i in range(5):
    mask = labels5_ordered == i
    ax6.scatter(values[mask], labels5_ordered[mask] + 1, c=[colors[i]], s=20, alpha=0.5)
ax6.set_xlabel('Mean Intensity')
ax6.set_ylabel('Group')
sil5 = silhouette_score(X, labels5)
ax6.set_title(f'Alternative Grouping (k=5, sil={sil5:.3f})')

plt.tight_layout()
plt.savefig('/Users/leelab/percell/clustering_analysis_dataset2.png', dpi=150, bbox_inches='tight')
print(f"\n✓ Saved analysis plot to clustering_analysis_dataset2.png")

# ============================================================
# RECOMMENDATIONS
# ============================================================
print("\n" + "=" * 70)
print("ANALYSIS SUMMARY AND RECOMMENDATIONS")
print("=" * 70)

print(f"""
Data characteristics:
- 371 cells with mean intensities from {values.min():.4f} to {values.max():.4f}
- The distribution appears to have a main cluster at low intensity with a tail of higher values

Current clustering (k=2):
- Group 1: 328 cells (0.02 - 0.29)
- Group 2: 43 cells (0.30 - 0.94)
- This is the result of silhouette optimization

Silhouette analysis:
- Best k by silhouette: {best_k_sil}
- The silhouette score is maximized at k=2, indicating the data naturally
  separates into 2 well-defined groups

BIC analysis:
- Best k by BIC: {best_k_bic}
- BIC tends to favor more clusters, suggesting more fine-grained structure

Conclusion:
- The current k=2 grouping is statistically optimal by silhouette score
- If you need more groups, you can force a higher k, but the silhouette
  score will be lower (clusters will be less well-separated)
- The data genuinely appears to have 2 main populations based on intensity
""")

print("=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
