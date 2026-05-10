#define _CRT_SECURE_NO_WARNINGS
#include<stdio.h>

int main() {
    int scores[10];
    int n = 10;
    int sum = 0;
    int count = 0;
    double average = 0.0;

    for (int i = 0; i < n; i++) {
        printf("请输入第%d个学生的成绩: ", i + 1);
        scanf("%d", &scores[i]);
        sum += scores[i];
        if (scores[i] > 90) {
            count++;
        }
    }

    average = (double)sum / n;

    printf("总成绩: %d\n", sum);
    printf("平均成绩: %.2f\n", average);
    printf("成绩大于90分的人数: %d\n", count);

    return 0;
}