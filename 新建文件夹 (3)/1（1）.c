#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>

int main() {
    char c1, c2;
    printf("请输入字符：");
    scanf_s("%c", &c1);
    c2 = (c1 >= 'a' && c1 <= 'z') ? c1 - 32 : c1 + 32;
    printf("字符转换的结果：%c", c2);
    return 0;
}