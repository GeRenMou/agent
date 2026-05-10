#define _CRT_SECURE_NO_WARNINGS
#include<stdio.h>
double jia(double x, double y) {
    return x + y;
}
double jian(double x, double y) {
    return x - y;
}
double chen(double x, double y) {
    return x * y;
}
double chu(double x, double y) {
    return x / y;
}
int main() {
    double x, y, z;
    char a;
    scanf("%lf%c%lf", &x, &a, &y);
    if (a == '+') {
        z = jia(x, y);
    }
    if (a == '-') {
        z = jian(x, y);
    }
    if (a == '*') {
        z = chen(x, y);
    }
    if (a == '/') {
        z = chu(x, y);
    }
    printf("%lf", z);
    return 0;
}