import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

fig, ax = plt.subplots(figsize=(6, 6))

# Grass
ax.add_patch(Rectangle((0, 0), 10, 1, facecolor="forestgreen", edgecolor="none"))

# House body
ax.add_patch(Rectangle((2, 1), 6, 5, facecolor="wheat", edgecolor="black"))

# Roof
ax.add_patch(Polygon([(1.5, 6), (5, 9), (8.5, 6)], facecolor="brown", edgecolor="black"))

# Door
ax.add_patch(Rectangle((4.2, 1), 1.6, 2.6, facecolor="saddlebrown", edgecolor="black"))

# Windows
ax.add_patch(Rectangle((2.8, 3.8), 1.3, 1.3, facecolor="skyblue", edgecolor="black"))
ax.add_patch(Rectangle((5.9, 3.8), 1.3, 1.3, facecolor="skyblue", edgecolor="black"))

ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("House with Grass")
plt.show()
