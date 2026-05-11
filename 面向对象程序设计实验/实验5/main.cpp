#include <iostream>
#include <cmath>
using namespace std;

class Point {
public:
    int x;
    int y;

    Point(int xCoord, int yCoord) : x(xCoord), y(yCoord) {}
};

class Rectangle {
public:
    Point bottomLeft;
    Point topRight;

    Rectangle(Point bl, Point tr) : bottomLeft(bl), topRight(tr) {}

    // 判断是否能构成矩形（两点不重合且不在同一水平/垂直线上）
    bool isRectangle() {
        return (bottomLeft.x != topRight.x) && (bottomLeft.y != topRight.y);
    }

    // 计算面积
    int area() {
        if (!isRectangle()) return 0;
        int width = abs(topRight.x - bottomLeft.x);
        int height = abs(topRight.y - bottomLeft.y);
        return width * height;
    }

    // 计算周长
    int perimeter() {
        if (!isRectangle()) return 0;
        int width = abs(topRight.x - bottomLeft.x);
        int height = abs(topRight.y - bottomLeft.y);
        return 2 * (width + height);
    }

    void display() {
        cout << "左下角: (" << bottomLeft.x << ", " << bottomLeft.y << ")" << endl;
        cout << "右上角: (" << topRight.x << ", " << topRight.y << ")" << endl;
        if (isRectangle()) {
            cout << "面积: " << area() << endl;
            cout << "周长: " << perimeter() << endl;
        } else {
            cout << "无法构成矩形！" << endl;
        }
    }
};

int main() {
    Point p1(0, 0);
    Point p2(5, 3);

    Rectangle rect(p1, p2);
    rect.display();

    return 0;
}
