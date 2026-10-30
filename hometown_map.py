"""把 places.csv 里的地点画成一张可交互地图。

用法：
    python hometown_map.py

输出：
    docs/index.html   地图网页（GitHub Pages 用这个文件）
    metrics.csv       每个地点到几何中心的距离
"""

from __future__ import annotations

import math
import sys
from itertools import combinations
from pathlib import Path

import folium
import pandas as pd

ROOT = Path(__file__).resolve().parent
PLACES_CSV = ROOT / "places.csv"
OUT_HTML = ROOT / "docs" / "index.html"
METRICS_CSV = ROOT / "metrics.csv"

# 高德栅格底图，无需 Key，坐标系 GCJ-02。
AMAP_TILES = (
    "https://webrd0{s}.is.autonavi.com/appmaptile"
    "?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}"
)
# folium 默认从 jsdelivr 加载 Leaflet，国内网络经常直接连不上。
# 生成完 HTML 后把这些地址换成国内可达的 bootcdn。
CDN_MIRROR = {
    "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.js":
        "https://cdn.bootcdn.net/ajax/libs/leaflet/1.9.4/leaflet.js",
    "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.css":
        "https://cdn.bootcdn.net/ajax/libs/leaflet/1.9.4/leaflet.css",
    "https://code.jquery.com/jquery-3.7.1.min.js":
        "https://cdn.bootcdn.net/ajax/libs/jquery/3.7.1/jquery.min.js",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js":
        "https://cdn.bootcdn.net/ajax/libs/twitter-bootstrap/5.2.2/js/bootstrap.bundle.min.js",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css":
        "https://cdn.bootcdn.net/ajax/libs/twitter-bootstrap/5.2.2/css/bootstrap.min.css",
    "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.2.0/css/all.min.css":
        "https://cdn.bootcdn.net/ajax/libs/font-awesome/6.2.0/css/all.min.css",
    "https://cdn.jsdelivr.net/gh/python-visualization/folium/folium/templates/leaflet.awesome.rotate.min.css":
        "",
}

# folium.Icon 只认固定颜色名，不能写十六进制色值。
CATEGORY_COLORS = {
    "家": "red",
    "学校": "blue",
    "交通": "green",
    "公园": "darkgreen",
    "医疗": "cadetblue",
    "商业": "orange",
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """两点间球面距离（km）。城市尺度误差小于 0.5%，够用。"""
    radius = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def load_places(path: Path) -> pd.DataFrame:
    """读 CSV，丢掉没填坐标的行，返回有效地点。"""
    if not path.exists():
        sys.exit(f"找不到 {path.name}。请在项目根目录运行本脚本。")

    try:
        df = pd.read_csv(path)
    except UnicodeDecodeError:
        # Excel 另存为 CSV 时可能是 GBK
        df = pd.read_csv(path, encoding="gbk")
        print("[提示] places.csv 是 GBK 编码，已兼容读取。"
              "建议用 VS Code 另存为 UTF-8，否则 GitHub 网页上会乱码。")

    missing = {"name", "category", "lon", "lat"} - set(df.columns)
    if missing:
        sys.exit(f"places.csv 缺少列：{', '.join(sorted(missing))}")

    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")

    blank = df["lon"].isna() | df["lat"].isna()
    if blank.any():
        names = "、".join(df.loc[blank, "name"].astype(str))
        print(f"[跳过] {blank.sum()} 个地点还没填经纬度：{names}")
    df = df.loc[~blank].reset_index(drop=True)

    if df.empty:
        sys.exit(
            "\n还没有任何有效坐标。\n"
            "打开 https://lbs.amap.com/tools/picker 搜地点，"
            "把「经度,纬度」填进 places.csv 的 lon、lat 两列，再运行一次。"
        )

    if (df["lat"].abs() > 90).any():
        sys.exit("有纬度绝对值超过 90，经纬度可能写反了：CSV 里 lon 在前，lat 在后。")

    return df


def add_basemap(m: folium.Map) -> None:
    # 只用高德。OSM 会拒绝 file:// 页面的瓦片请求，返回 403。
    folium.TileLayer(
        tiles=AMAP_TILES,
        name="高德底图",
        attr="高德地图",
        subdomains="1234",
        max_zoom=18,
    ).add_to(m)


def build_map(df: pd.DataFrame) -> tuple[folium.Map, tuple[float, float]]:
    center_lat = float(df["lat"].mean())
    center_lon = float(df["lon"].mean())

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles=None,
        control_scale=True,
    )
    add_basemap(m)

    # 5 km 缓冲圈：P1「15 分钟生活圈」的雏形。
    folium.Circle(
        location=[center_lat, center_lon],
        radius=5000,
        color="#d35400",
        weight=1,
        fill=False,
        dash_array="6",
        tooltip="以几何中心为圆心，5 km",
    ).add_to(m)

    for row in df.itertuples(index=False):
        dist = haversine_km(center_lat, center_lon, row.lat, row.lon)
        folium.Marker(
            location=[row.lat, row.lon],
            tooltip=str(row.name),
            popup=folium.Popup(
                f"<b>{row.name}</b><br>类别：{row.category}"
                f"<br>距几何中心：{dist:.1f} km",
                max_width=220,
            ),
            icon=folium.Icon(
                color=CATEGORY_COLORS.get(str(row.category), "gray"),
                icon="info-sign",
            ),
        ).add_to(m)

    if len(df) > 1:
        m.fit_bounds(
            [
                [float(df["lat"].min()), float(df["lon"].min())],
                [float(df["lat"].max()), float(df["lon"].max())],
            ]
        )

    folium.LayerControl().add_to(m)
    return m, (center_lat, center_lon)


def summarize(df: pd.DataFrame, center: tuple[float, float]) -> pd.DataFrame:
    lat0, lon0 = center
    out = df.copy()
    out["dist_km"] = [
        haversine_km(lat0, lon0, float(row.lat), float(row.lon))
        for row in df.itertuples(index=False)
    ]
    return out[["name", "category", "lon", "lat", "dist_km"]].sort_values("dist_km")


def warn_outliers(df: pd.DataFrame, threshold_km: float = 50.0) -> None:
    """坐标写错时（比如搜到外地同名地点）给一个醒目提醒。"""
    lat0 = float(df["lat"].median())
    lon0 = float(df["lon"].median())

    far = []
    for row in df.itertuples(index=False):
        dist = haversine_km(lat0, lon0, float(row.lat), float(row.lon))
        if dist > threshold_km:
            far.append((str(row.name), dist))

    if not far:
        return

    print("[警告] 下面这些点离其余点超过 50 km，很可能是搜到了外地同名地点：")
    for name, dist in far:
        print(f"  - {name}：{dist:.0f} km")
    print("  核对经纬度，或把该行 lon、lat 清空后重跑。\n")


def patch_cdn(html_path: Path) -> None:
    """把 folium 写死的国外 CDN 换掉，否则国内打开是空白。"""
    html = html_path.read_text(encoding="utf-8")
    replaced = 0
    for old, new in CDN_MIRROR.items():
        if old in html:
            html = html.replace(old, new)
            replaced += 1
    html_path.write_text(html, encoding="utf-8")
    print(f"[CDN] 替换了 {replaced} 个国外静态资源地址")
    if "cdn.jsdelivr.net" in html:
        print("[提示] 页面里还有 jsdelivr 地址，国内可能加载失败。")


def main() -> None:
    df = load_places(PLACES_CSV)
    warn_outliers(df)
    m, center = build_map(df)

    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(OUT_HTML))
    patch_cdn(OUT_HTML)

    metrics = summarize(df, center)
    metrics.to_csv(METRICS_CSV, index=False, encoding="utf-8-sig")

    print(f"\n共 {len(df)} 个地点，几何中心 ({center[0]:.4f}, {center[1]:.4f})")
    far = metrics.iloc[-1]
    print(f"最远的地点：{far['name']}，{far['dist_km']:.1f} km")

    if len(df) > 1:
        best = max(
            (
                (a.name, b.name, haversine_km(a.lat, a.lon, b.lat, b.lon))
                for a, b in combinations(list(df.itertuples(index=False)), 2)
            ),
            key=lambda item: item[2],
        )
        print(f"相距最远的两点：{best[0]} 到 {best[1]}，{best[2]:.1f} km")

    print("\n| 地点 | 类别 | 到中心距离 (km) |")
    print("| --- | --- | --- |")
    for row in metrics.itertuples(index=False):
        print(f"| {row.name} | {row.category} | {row.dist_km:.1f} |")

    print(f"\n地图已生成：{OUT_HTML.relative_to(ROOT)}")
    print(f"距离表已生成：{METRICS_CSV.name}")
    print("双击 docs/index.html 就能看。下一步：commit + push，开 GitHub Pages。")


if __name__ == "__main__":
    main()
