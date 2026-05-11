#include <iostream>
using namespace std;

class Factorial {
private:
    int value;
    long long fact;

public:
    Factorial(int n) : value(n), fact(1) {}

    void calculateFactorial() {
        fact = 1;
        for (int i = 1; i <= value; i++) {
            fact *= i;
        }
    }

    void displayResult() {
        cout << value << "! = " << fact << endl;
    }
};

int main() {
    int n;
    cout << "请输入一个正整数: ";
    cin >> n;

    Factorial f(n);
    f.calculateFactorial();
    f.displayResult();

    return 0;
}
