#include <iostream>
#include <vector>
#include <iomanip>
using namespace std;

class Product {
private:
    int id;
    double price;
    double discount;

    static double totalSum;    // 总销售额
    static int totalSales;     // 总销售数量

public:
    Product(int id, double p, double d) : id(id), price(p), discount(d) {}

    // 计算单件商品的销售（折后价 * 1件）
    void calculateSales() {
        double salesPrice = price * (1 - discount / 100.0);
        totalSum += salesPrice;
        totalSales++;
    }

    static double getAveragePrice() {
        if (totalSales == 0) return 0;
        return totalSum / totalSales;
    }

    static void displaySummary() {
        cout << fixed << setprecision(2);
        cout << "总销售额: " << totalSum << endl;
        cout << "总销售数量: " << totalSales << endl;
        cout << "平均价格: " << getAveragePrice() << endl;
    }

    void display() const {
        cout << "商品ID: " << id
             << ", 原价: " << price
             << ", 折扣: " << discount << "%" << endl;
    }
};

// 静态成员初始化
double Product::totalSum = 0;
int Product::totalSales = 0;

int main() {
    vector<Product> products;

    // 添加5个商品
    products.push_back(Product(101, 5, 23.5));
    products.push_back(Product(102, 12, 24.56));
    products.push_back(Product(103, 100, 21.5));
    products.push_back(Product(104, 50, 10.0));
    products.push_back(Product(105, 80, 15.0));

    cout << "所有商品信息:" << endl;
    for (const auto& p : products) {
        p.display();
    }

    // 计算销售
    for (auto& p : products) {
        p.calculateSales();
    }

    cout << "\n销售汇总:" << endl;
    Product::displaySummary();

    return 0;
}
