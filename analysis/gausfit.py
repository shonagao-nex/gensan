######################################################################################
# KSpectで取得したデータをフィットするサンプルコートです。
# Ge検出器で得られた光電ピークを想定していますが、パラメータを調整すれば一般的に利用できます。
### 使い方 ###
# 1. L14  読み込みファイルfile_path を変更し
# 2. L26~28  フィット範囲、初期パラメータ、パラメータを振る範囲を設定する
# 3. 実行＆結果を確認
# エラーが発生した場合は、エラー出力をよく読んで対応すること
# 描画範囲などを設定したい場合は、L96~108 を適宜変更する
######################################################################################
# ライブラリの読み込み
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import math

# 入力ファイル名
file_path = 'co60.spe'

# フィットで用いる関数形の定義（正規分布 + バックグラウンド一次関数）
# p0, p1, p2 = 正規分布の面積、ピーク位置、幅（rms）
# p3, p4     = 一次関数の傾き、切片
def fit_func(x, p0, p1, p2, p3, p4):
    gauss = (p0 / (np.sqrt(2 * np.pi) * p2)) * np.exp(-(x - p1)**2 / (2 * p2**2))
    f1 = p3 * x + p4
    return gauss + f1

# パラメータ定義
fit_range = [3400, 3520]            # フィット範囲の定義
p_init = [1000, 3480, 10, 0.0, 10]  # 初期パラメータ設定、詳細はfit_funcを参照
p_range = ([0, 3400, 1, -10, 0], [1000000, 3600, 50, 10, 10000]) # パラメータの探索範囲（範囲は初期パラメータを含むように定義する）
print("#############################")
print("Initial parameters:")
for i, initial in enumerate(p_init):
    print(f"  p{i}: {initial:.2e}")
print("#############################")

# ファイルの読み込み
# ヒストグラム作成に必要なデータのみを抽出して data に格納する。
try:
    with open(file_path, 'r') as file:
        lines = file.readlines()
    # データ開始行と終了行を特定
    start_index = next(i for i, line in enumerate(lines) if line.strip() == "0 4095") + 1
    end_index = next(i for i, line in enumerate(lines) if line.strip().startswith("$ENER_FIT:"))
    # データを抽出
    data = [int(line.strip()) for line in lines[start_index:end_index]]
except FileNotFoundError:
    print(f"Error: The file '{file_path}' does not exist.")
    exit()
except Exception as e:
    print(f"An error occurred: {e}")
    exit()

# データを扱いやすいように格納
x_data_full   = np.arange(len(data))
y_data_full   = np.array(data)
y_err_full = np.sqrt(y_data_full)
x_data   = np.arange(fit_range[0], fit_range[1])
y_data   = np.array(data[fit_range[0]:fit_range[1]])
y_data   = np.where(y_data <= 0, 0.0001, y_data) # カウント数が0の場合におけるエラー対策
y_err = np.sqrt(y_data)                       # 各データ点の誤差（平方根を誤差として使用）重要！！

# フィッティング
try:
    # フィットを実行し、結果をpoptに、共分散をpcovにつめる
    popt, pcov = curve_fit(fit_func, x_data, y_data, sigma=y_err, absolute_sigma=True, p0=p_init, bounds=p_range)
    residuals = y_data - fit_func(x_data, *popt)      # 残差を計算
    chi_squared = np.sum((residuals / y_err) ** 2) # カイ二乗を計算
    reduced_chi_squared = chi_squared / (len(x_data) - len(popt)) # 換算カイ二乗 = カイ二乗 / 自由度
    p_err = np.sqrt(np.diag(pcov))                 # 共分散行列からパラメータ誤差を計算

    # フィットの結果を表示
    print("Fitted Results")
    for i, (param, error) in enumerate(zip(popt, p_err)):
        significant_digits = -int(math.floor(math.log10(error))) + 2   # 桁あわせ
        format_string = f"  p{i}: {{:10.{significant_digits}f}} ±{error:10.{significant_digits}f}"
        print(format_string.format(param))
    print("Chi-squared: {:.3e}".format(chi_squared))
    print("Reduced Chi-squared: {:.3f}".format(reduced_chi_squared))
    print("#############################")
except Exception as e:
    # フィットに失敗した場合はヒストグラムだけ描画する
    print(f"Error in fitting: {e}")
    print("Check input parameters")
    plt.figure(figsize=(10, 6))
    plt.hist(x_data_full, weights=y_data_full, bins=len(data), histtype='step', linewidth=1.0, color='black', fill=True, facecolor='none')
    plt.title('Spectrum Histogram', fontsize=20, pad=20)
    plt.xlabel('Channel', fontsize=30)
    plt.ylabel('Counts', fontsize=30)
    plt.xlim(0, len(data))
    plt.subplots_adjust(left=0.10, right=0.95, top=0.90, bottom=0.10)
    plt.yscale('log')

# プロット
plt.figure(figsize=(10, 6))  # 描画サイズ
plt.errorbar(x_data_full, y_data_full, yerr=y_err_full, fmt='o', label='Data', ecolor='black', alpha=0.5)  # 誤差棒を含めたヒストグラムプロット
plt.plot(x_data, fit_func(x_data, *popt), label='Fit', color='red') # フィット結果のプロット
plt.title('Histogram Title', fontsize=20, pad=20)         # ヒストグラムタイトル
plt.xlabel('Channel', fontsize=26)                        # 横軸タイトル
plt.ylabel('Counts', fontsize=26)                         # 縦軸タイトル
plt.tick_params(axis='both', which='major', labelsize=18) # 軸ラベルの設定
#plt.xlim(0, len(data))                                    # X軸の描画範囲設定（全範囲を描画）
plt.xlim(fit_range[0] - 10, fit_range[1]+10)              # X軸の描画範囲設定（フィット範囲付近）
plt.ylim(0.8, max(data)*1.1)                              # Y軸の描画範囲設定
plt.subplots_adjust(left=0.15, right=0.95, top=0.90, bottom=0.15) # マージン設定
plt.yscale('log')                                         # ログ設定
plt.legend(fontsize=18)                                   # 凡例の設定
plt.show()
