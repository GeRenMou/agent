#include <iostream>
using namespace std;

// 函数重载：两个 print 函数
void print(int x) {
    cout << "调用 print(int x), x = " << x << endl;
}

void print(int x, int y = 10) {
    cout << "调用 print(int x, int y = 10), x = " << x << ", y = " << y << endl;
}

int main() {
    /*
     * 分析：当调用 print(5) 时会发生什么？
     *
     * void print(int x)            —— 需要一个 int 参数
     * void print(int x, int y = 10) —— 需要一到两个 int 参数
     *
     * print(5) 可以匹配两个函数：
     *   - print(int x)：精确匹配
     *   - print(int x, int y = 10)：第二个参数使用默认值，也匹配
     *
     * 因此编译器会报错：error C2668: 对重载函数的调用不明确
     *
     * 如需编译运行，请注释掉下面这行，并取消另一段的注释
     */

    // ===== 此调用会产生歧义，编译不通过 =====
    // print(5);

    // ===== 明确调用的方式 =====
    print(5, 20);  // 明确调用 print(int, int)，输出两个参数

    return 0;
}
