#define _CRT_SECURE_NO_WARNINGS
#include<stdio.h>

int main() {
    int n;
    scanf("%d", &n);

    if (n >= 90) {
        printf("等级为优");
    }
    else if (n < 90 && n >= 80) {
        printf("等级为良");
    }
    else if (n < 80 && n >= 70) {
        printf("等级为中");
    }
    else if (n < 70 && n >= 60) {
        printf("等级为及格");
    }
    else if (n < 60) {
        printf("等级为不及格");
    }
    return 0;
}