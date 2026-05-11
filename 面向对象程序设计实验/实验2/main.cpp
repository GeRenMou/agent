#include <iostream>
using namespace std;

// 求 n 的所有真因子之和（真因子：小于 n 的正整数中能整除 n 的数）
int sumOfFactors(int n) {
    int sum = 0;
    for (int i = 1; i <= n / 2; i++) {
        if (n % i == 0) {
            sum += i;
        }
    }
    return sum;
}

int main() {
    int n;
    cout << "请输入一个整数 n (1 < n <= 1000): ";
    cin >> n;

    if (n <= 1 || n > 1000) {
        cout << "输入不合法！n 应在 (1, 1000] 范围内。" << endl;
        return 1;
    }

    int result = sumOfFactors(n);
    cout << n << " 的真因子之和为: " << result << endl;

    return 0;
}
