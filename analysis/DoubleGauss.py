# ==============================================================
# KSpect .spe フィットツール（Plotly表示版）
# --------------------------------------------------------------
# 【概要】
#   KSpect で取得した .spe スペクトルデータを読み込み、
#   単一ピークを「ガウス2個 + 1次関数（傾き + 切片）」でフィットします。
#
# 【使い方】
#   1. Google Colab 上でこのセルを実行します。
#   2. `file_path` を解析したい .spe ファイルに変更してください。
#        例: file_path = '/content/data.spe'
#   3. `mu` と `sigma` にピーク位置と概形の推定値を入力します。
#   4. `fit_range` に解析したいチャンネル範囲を指定します。
#        例: fit_range = [1550, 1650]
#   5. 実行すると：
#        ・コンソールにフィット結果（パラメータ・誤差・自由度など）
#        ・ブラウザ上にスペクトル＋フィット曲線が表示されます。
#   6. 図の上部ボタンで Y 軸を
#        「Linear Y」 / 「Log Y」 に切り替え可能。
#
# 【パラメータの意味】
#   p0 (area1)       : ガウス面積（積分強度）
#   p1 (mu1)         : ガウス中心チャンネル
#   p2 (sigma1)      : ガウス幅（標準偏差）
#   p3 (area2)       : ガウス面積（積分強度）
#   p4 (mu2)         : ガウス中心チャンネル
#   p5 (sigma2)      : ガウス幅（標準偏差）
#   p6 (intercept)  : バックグラウンドの切片
#   p7 (slope)      : バックグラウンドの傾き
#   Chi-squared     : カイ二乗値
#   Reduced Chi2    : カイ二乗/自由度
#   DoF             : 自由度
# ==============================================================
# -------- ライブラリインポート（変更不要） ----------
!pip -q install plotly
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import curve_fit
import math, os

# -------- 初期設定（要変更） --------
file_path = '/content/Ge1_Co60Ra226_115mm.spe'   # <--- 解析したいファイルを入力
mu1 = 2829                                   # <--- 読み取ったピークの中心値を入力
sigma1 = 4                                   # <--- 読み取ったピークの幅を入力
mu2 = 3211                                   # <--- 読み取ったピークの中心値を入力
sigma2 = 4                                   # <--- 読み取ったピークの幅を入力
fit_range = [2700, 3300]                     # <--- フィットしたいレンジを入力
# -------- 図タイトル（要変更） --------
Title  = 'Title'
TitleX = 'X Title'
TitleY = 'Y Title'
# -------- 初期設定（状況に応じて変更） --------
p_init    = [1000, mu1, sigma1, 1000, mu2, sigma2, 10, 0.0]
p_bounds  = ([0, mu1 - 2.0 * sigma1, 1, 0, mu2 - 2.0 * sigma2, 1, 0, -10], [1_000_000, mu1 + 2.0 * sigma1, 4 * sigma1, 1_000_000, mu2 + 2.0 * sigma2, 4 * sigma2, 10_000, 10])

# -------- フィット関数 --------
def fit_func(x, p0, p1, p2, p3, p4, p5, p6, p7):
    gauss1 = (p0 / (np.sqrt(2*np.pi) * p2)) * np.exp(-(x - p1)**2 / (2 * p2**2))
    gauss2 = (p3 / (np.sqrt(2*np.pi) * p5)) * np.exp(-(x - p4)**2 / (2 * p5**2))
    bg    = p6 + p7 * x
    return gauss1 + gauss2 + bg

# ==============================================================
# 以下のコードは変更不要、ただしコードで何をやっているか概要を理解しておくこと。
# 特に、「フィット」「フィット結果の出力」部分に関しては詳細まで理解を深めておくこと。
# ==============================================================
# -------- .spe 読み込み --------
if not os.path.exists(file_path):
    raise FileNotFoundError(f"入力ファイルが見つかりません: {file_path}")

with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

start_index = next(i for i, line in enumerate(lines) if line.strip() == "0 4095") + 1
end_index   = next(i for i, line in enumerate(lines) if line.strip().startswith("$ENER_FIT:"))

# 行頭末の空白やコメントを無視しつつ整数だけ抽出
data = []
for s in (ln.strip() for ln in lines[start_index:end_index]):
    if s and s.replace('-', '').isdigit():
        data.append(int(s))

if not data:
    raise RuntimeError("スペクトルデータが空です。")

data      = np.array(data, dtype=float)
x_full    = np.arange(len(data))
y_full    = data
yerr_full = np.sqrt(np.clip(y_full, 0, None))

# -------- フィット対象抽出 --------
xmin, xmax = fit_range
if xmin < 0 or xmax > len(data) or xmin >= xmax:
    raise ValueError(f"fit_rangeが不正です: {fit_range} / N={len(data)}")

x_fit      = np.arange(xmin, xmax)
y_fit      = data[xmin:xmax]
y_fit_safe = np.where(y_fit <= 0, 1e-4, y_fit)
yerr_fit   = np.sqrt(y_fit_safe)

# -------- フィット --------
popt, pcov = curve_fit(
    fit_func, x_fit, y_fit_safe,
    sigma=yerr_fit, absolute_sigma=True,
    p0=p_init, bounds=p_bounds, maxfev=20000
)
perr = np.sqrt(np.diag(pcov))
chi2 = np.sum(((y_fit - fit_func(x_fit, *popt)) / np.sqrt(y_fit_safe))**2)
dof  = max(1, len(x_fit) - len(popt))
rchi2 = chi2 / dof
dof = max(1, len(x_fit) - len(popt))

# -------- フィット結果の出力 --------
names = ["p0 (area1)", "p1 (mu1)", "p2 (sigma1)", "p3 (area2)", "p4 (mu2)", "p5 (sigma2)", "p6 (intercept)", "p7 (slope)"]

print("\nFitted Results")
print(f"  DoF                 : {dof:d}")
print(f"  Chi-squared         : {chi2:.4e}")
print(f"  Reduced Chi-squared : {rchi2:.4e}")

print("\n  Parameter           Value (exp)        Uncertainty (exp)")
print("  --------------------------------------------------------")
for name, val, err in zip(names, popt, perr):
    print(f"  {name:<16s} {val:>14.4e}    ± {err:>14.4e}")
print("  --------------------------------------------------------\n")

# -------- レンジとログ目盛の安定化 --------
linear_top = float(max(1.0, np.max(y_full) * 1.1))  # リニア上限

# ログレンジ上限
max_pos = np.max(y_full[y_full > 0]) if np.any(y_full > 0) else 1.0
log_top_decade = int(np.ceil(np.log10(max(10.0, max_pos * 1.1))))
log_tickvals = [10**k for k in range(0, log_top_decade + 1)]
log_range = [0, log_top_decade]  # 1 〜 10^N（下限は1固定）

# -------- Plotly描画 --------
fig = go.Figure()

# データ点設定
fig.add_trace(go.Scatter(
    x=x_full, y=y_full,
    mode='markers',
    marker=dict(size=4, color='black', symbol='circle', opacity=0.9),
    error_y=dict(type='data', array=yerr_full, color='black', thickness=1.2, visible=True),
    hovertemplate="Channel=%{x}<br>Counts=%{y}<extra></extra>"
))

# フィット線をスムーズに
x_fit_smooth = np.linspace(xmin, xmax, 1000)
fig.add_trace(go.Scatter(
    x=x_fit_smooth,
    y=fit_func(x_fit_smooth, *popt),
    mode='lines',
    line=dict(width=2, color='red'),
    hovertemplate="Fit y=%{y:.3f}<extra></extra>"
))

# レイアウト設定
title_text = os.path.basename(file_path)
fig.update_layout(
    template="simple_white",
#    title=title_text,
    title=Title,
    font=dict(family="Arial", size=14, color="black"),
    paper_bgcolor="white", plot_bgcolor="white",
#    xaxis_title="Channel", yaxis_title="Counts",
    xaxis_title=TitleX, yaxis_title=TitleY,
    xaxis_title_font=dict(size=28), yaxis_title_font=dict(size=28),
    hovermode="x unified",
    showlegend=False,
    margin=dict(l=80, r=30, t=60, b=70),
    width=900, height=600,
    updatemenus=[
        dict(
            type="buttons", direction="right",
            x=0.5, y=1.12, xanchor="center", yanchor="top",
            pad={"r": 10, "t": 6},
            buttons=[
                dict(
                    label="Log Y",
                    method="relayout",
                    args=[{
                        "yaxis.type": "log",
                        "yaxis.range": log_range,
                        "yaxis.tickvals": log_tickvals,
                        "yaxis.ticktext": [("1" if v==1 else f"1e{int(np.log10(v))}") for v in log_tickvals]
                    }]
                ),
                dict(
                    label="Linear Y",
                    method="relayout",
                    args=[{
                        "yaxis.type": "linear",
                        "yaxis.range": [0, linear_top],
                        "yaxis.tickvals": None,
                        "yaxis.ticktext": None
                    }]
                ),
            ],
        )
    ]
)

# 軸スタイル設定
axis_style = dict(
    range=[0, 4096],
    showline=True, linewidth=1.2, linecolor="black", mirror=True,
    ticks="outside", tickwidth=1, ticklen=6,
    tickfont=dict(size=20),
    showgrid=False, gridcolor="#dddddd", gridwidth=1,
    zeroline=False
)
fig.update_xaxes(**axis_style)
y_axis_style = {k: v for k, v in axis_style.items() if k != "range"}
fig.update_yaxes(**y_axis_style)

fig.show()
