#define _CRT_SECURE_NO_WARNINGS
#include<stdio.h>

struct Student {
    char name[20];
    char phone[15];
};

int main() {
    struct Student stu[3];
    for (int i = 0; i < 3; i++) {
        printf("请输入第%d个学生信息：\n", i + 1);
        printf("姓名：");
        scanf("%s", stu[i].name);
        printf("电话：");
        scanf("%s", stu[i].phone);
    }

    printf("\n学生通讯录：\n");
    for (int i = 0; i < 3; i++) {
        printf("%s - %s\n", stu[i].name, stu[i].phone);
    }
    return 0;
}
