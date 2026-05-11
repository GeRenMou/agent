#include <iostream>
#include <cmath>
using namespace std;

class Point {
public:
    int x;
    int y;

    Point(int xCoord, int yCoord) : x(xCoord), y(yCoord) {}
};

class Circle {
private:
    float* radius;
    Point center;

public:
    Circle(float r, Point c) : center(c) {
        radius = new float(r);
    }

    // 拷贝构造
    Circle(const Circle& other) : center(other.center) {
        radius = new float(*other.radius);
    }

    // 析构函数
    ~Circle() {
        delete radius;
    }

    float getRadius() const { return *radius; }
    Point getCenter() const { return center; }

    // 判断两个圆的关系
    static void determineRelationship(const Circle& c1, const Circle& c2) {
        // 计算圆心距离
        float dx = (float)(c1.center.x - c2.center.x);
        float dy = (float)(c1.center.y - c2.center.y);
        float distance = sqrt(dx * dx + dy * dy);

        float sumRadii = c1.getRadius() + c2.getRadius();
        float diffRadii = fabs(c1.getRadius() - c2.getRadius());

        cout << "圆心距离: " << distance << endl;
        cout << "半径之和: " << sumRadii << endl;
        cout << "半径之差: " << diffRadii << endl;

        if (distance == 0 && diffRadii == 0) {
            cout << "关系: 两圆重合（同心等半径）" << endl;
        } else if (distance == 0 && diffRadii != 0) {
            cout << "关系: 同心圆" << endl;
        } else if (distance > sumRadii) {
            cout << "关系: 相离" << endl;
        } else if (distance == sumRadii) {
            cout << "关系: 外切" << endl;
        } else if (distance > diffRadii && distance < sumRadii) {
            cout << "关系: 相交" << endl;
        } else if (distance == diffRadii) {
            cout << "关系: 内切" << endl;
        } else if (distance < diffRadii) {
            cout << "关系: 内含" << endl;
        }
    }

    void display() const {
        cout << "圆心: (" << center.x << ", " << center.y
             << "), 半径: " << *radius << endl;
    }
};

int main() {
    Circle c1(5.0f, Point(0, 0));
    Circle c2(3.0f, Point(4, 0));

    cout << "圆1: "; c1.display();
    cout << "圆2: "; c2.display();
    cout << endl;

    Circle::determineRelationship(c1, c2);

    return 0;
}
