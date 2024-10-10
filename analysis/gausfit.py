import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import math

def combined_func(x, p0, p1, p2, p3, p4):
    gauss = (p0 / (np.sqrt(2 * np.pi) * p2)) * np.exp(-(x - p1)**2 / (2 * p2**2))
    f1 = p3 * x + p4
    return gauss + f1

# 初期パラメータの推測とバウンズ
fit_min = 3400
fit_max = 3520
p_init = [1000, 3480, 10, -0.01, 100]
p_range = ([0, 3400, 1, -10, 0], [1000000, 3600, 50, 0, 10000])

print("Initial parameters:")
for i, initial in enumerate(p_init):
    print(f"  p{i}: {initial:.2e}")

# ファイルの内容を読み込む
file_path = 'co60.txt'
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

# データの全範囲
x_data_full = np.arange(len(data))
y_data_full = np.array(data)

# フィットするデータ範囲の選択
x_data = np.arange(fit_min, fit_max)
y_data = np.array(data[fit_min:fit_max])
y_data = np.where(y_data <= 0, 0.0001, y_data)
y_errors = np.sqrt(y_data)  # 各データ点の誤差（平方根を誤差として使用）

# フィッティング試行
try:
    popt, pcov = curve_fit(combined_func, x_data, y_data, sigma=y_errors, absolute_sigma=True, p0=p_init, bounds=p_range)
    residuals = y_data - combined_func(x_data, *popt)
    chi_squared = np.sum((residuals / y_errors) ** 2)
    reduced_chi_squared = chi_squared / (len(x_data) - len(popt))
    p_errors = np.sqrt(np.diag(pcov))

    print("Fitted parameters:")
    for i, (param, error) in enumerate(zip(popt, p_errors)):
        # 最も有意な桁で中央値を表示
        significant_digits = -int(math.floor(math.log10(error))) + 2
        format_string = f"  p{i}: {{:10.{significant_digits}f}} ±{error:10.{significant_digits}f}"
        print(format_string.format(param))

    print("Chi-squared: {:.3e}".format(chi_squared))
    print("Reduced Chi-squared: {:.3f}".format(reduced_chi_squared))
except Exception as e:
    print(f"Error in fitting: {e}")
    exit()

# プロット
plt.figure(figsize=(16, 10))
plt.hist(x_data_full, weights=y_data_full, bins=len(data), histtype='step', linewidth=1.0, color='black', fill=True, facecolor='none')
#plt.errorbar(x_data, y_data, yerr=y_errors, fmt='o', label='Data with errors in fit range', ecolor='red', alpha=0.5)
plt.plot(x_data, combined_func(x_data, *popt), label='Fit Line', color='red')
plt.title('Spectrum Histogram', fontsize=26, pad=26)
plt.xlabel('Channel', fontsize=30)
plt.ylabel('Counts', fontsize=30)
plt.tick_params(axis='both', which='major', labelsize=20)
plt.xlim(0, len(data))
#plt.ylim(8, max(data)*1.1)
plt.subplots_adjust(left=0.10, right=0.95, top=0.90, bottom=0.10)
plt.yscale('log')
plt.legend(fontsize=24)
plt.show()
