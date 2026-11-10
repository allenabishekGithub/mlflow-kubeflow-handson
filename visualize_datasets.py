"""Visualize the datasets and train/test splits used by the two demo scripts.

This only recreates and plots the data. It does not train models or contact MLflow.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from sklearn.datasets import make_circles, make_classification
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


CLASS_COLORS = {0: "#2469a0", 1: "#e58626"}


def classification_data():
    """Recreate the data and split in mlflow_ml_demo.py."""
    features, labels = make_classification(
        n_samples=1000,
        n_features=12,
        n_informative=8,
        n_redundant=2,
        random_state=42,
    )
    return train_test_split(
        features,
        labels,
        test_size=0.2,
        stratify=labels,
        random_state=42,
    )


def circles_data():
    """Recreate the data and split in pytorch_dl_demo.py."""
    features, labels = make_circles(
        n_samples=1200,
        noise=0.12,
        factor=0.45,
        random_state=42,
    )
    return train_test_split(
        features,
        labels,
        test_size=0.2,
        stratify=labels,
        random_state=42,
    )


def draw_split(axis, train_features, test_features, train_labels, test_labels):
    """Use color for class and a hollow marker for held-out test examples."""
    for label, color in CLASS_COLORS.items():
        train = train_features[train_labels == label]
        test = test_features[test_labels == label]
        axis.scatter(
            train[:, 0],
            train[:, 1],
            s=17,
            color=color,
            alpha=0.45,
            linewidths=0,
            zorder=1,
        )
        axis.scatter(
            test[:, 0],
            test[:, 1],
            s=38,
            facecolors="none",
            edgecolors=color,
            linewidths=1.1,
            alpha=0.85,
            zorder=2,
        )
    axis.grid(alpha=0.2)


def print_counts(name, train_labels, test_labels):
    """Make the plotted split and class balance explicit in the terminal."""
    train_counts = {label: int((train_labels == label).sum()) for label in CLASS_COLORS}
    test_counts = {label: int((test_labels == label).sum()) for label in CLASS_COLORS}
    print(
        f"{name}: train={len(train_labels)} {train_counts}; "
        f"test={len(test_labels)} {test_counts}"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "datasets.png",
        help="Image path (default: datasets.png next to this script)",
    )
    parser.add_argument("--show", action="store_true", help="Also open an interactive plot window")
    args = parser.parse_args()

    ml_train, ml_test, ml_train_y, ml_test_y = classification_data()
    dl_train, dl_test, dl_train_y, dl_test_y = circles_data()
    print_counts("ML classification", ml_train_y, ml_test_y)
    print_counts("DL circles", dl_train_y, dl_test_y)

    # The ML model uses all 12 original features. PCA is only a 2D view for people.
    projection = PCA(n_components=2).fit(ml_train)
    ml_train_2d = projection.transform(ml_train)
    ml_test_2d = projection.transform(ml_test)

    # Match the PyTorch demo: fit scaling on training data, then transform both splits.
    scaler = StandardScaler().fit(dl_train)
    dl_train_scaled = scaler.transform(dl_train)
    dl_test_scaled = scaler.transform(dl_test)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.4))
    draw_split(axes[0], ml_train_2d, ml_test_2d, ml_train_y, ml_test_y)
    axes[0].set_title("ML: classification data (1,000 rows)")
    axes[0].set_xlabel(f"PCA component 1 ({projection.explained_variance_ratio_[0]:.0%} variance)")
    axes[0].set_ylabel(f"PCA component 2 ({projection.explained_variance_ratio_[1]:.0%} variance)")

    draw_split(axes[1], dl_train, dl_test, dl_train_y, dl_test_y)
    axes[1].set_title("DL: circles before scaling (1,200 rows)")
    axes[1].set_xlabel("Original x coordinate")
    axes[1].set_ylabel("Original y coordinate")
    axes[1].set_aspect("equal", adjustable="box")

    draw_split(axes[2], dl_train_scaled, dl_test_scaled, dl_train_y, dl_test_y)
    axes[2].set_title("DL: circles after scaling")
    axes[2].set_xlabel("Scaled x coordinate")
    axes[2].set_ylabel("Scaled y coordinate")
    axes[2].set_aspect("equal", adjustable="box")

    legend = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=CLASS_COLORS[0],
               markeredgecolor=CLASS_COLORS[0], markersize=8, label="Class 0 (filled = train)"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=CLASS_COLORS[1],
               markeredgecolor=CLASS_COLORS[1], markersize=8, label="Class 1 (filled = train)"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="none",
               markeredgecolor="#555555", markersize=8, label="Hollow = held-out test"),
    ]
    fig.legend(
        handles=legend,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.055),
        ncol=3,
        frameon=False,
    )
    fig.suptitle("The datasets used by the MLflow quickstart demos", fontsize=15)
    fig.text(
        0.5,
        0.02,
        "The ML panel shows a 2D PCA projection; the model trains on all 12 features. "
        "The circles panels show the actual two features used by the neural network.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.15, 1, 0.92))

    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, bbox_inches="tight")
    print(f"Saved plot to {output}")
    if args.show:
        plt.show()
    plt.close(fig)


if __name__ == "__main__":
    main()
