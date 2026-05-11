#include <iostream>
using namespace std;

class CBank {
private:
    double balance;

public:
    CBank(double bal) : balance(bal) {}

    friend double total(const CBank& cBank, const class IBank& iBank, const class ABank& aBank);
};

class IBank {
private:
    double balance;

public:
    IBank(double bal) : balance(bal) {}

    friend double total(const CBank& cBank, const IBank& iBank, const class ABank& aBank);
};

class ABank {
private:
    double balance;

public:
    ABank(double bal) : balance(bal) {}

    friend double total(const CBank& cBank, const IBank& iBank, const ABank& aBank);
};

// 友元函数：计算三家银行余额总和
double total(const CBank& cBank, const IBank& iBank, const ABank& aBank) {
    return cBank.balance + iBank.balance + aBank.balance;
}

int main() {
    CBank c(1000.50);
    IBank i(2000.75);
    ABank a(3000.25);

    cout << "CBank 余额: 1000.50" << endl;
    cout << "IBank 余额: 2000.75" << endl;
    cout << "ABank 余额: 3000.25" << endl;
    cout << "三家银行总余额: " << total(c, i, a) << endl;

    return 0;
}
