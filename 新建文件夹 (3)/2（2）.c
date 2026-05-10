#define _CRT_SECURE_NO_WARNINGS
#define PI 3.14159
#include<stdio.h>

int main() {
    float r = 0, d = 0, s = 0;
    scanf("%f", &r);
    d = 2 * r;          // 直径
    s = PI * 2 * r;     // 周长
    printf("直径=%f\n周长=%f", d, s);
    return 0;
}