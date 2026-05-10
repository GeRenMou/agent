#include <stdio.h>
#include <string.h>
#include <stdlib.h>  // 添加这个头文件用于清屏

// 1. 定义图书结构体
struct Book {
    int id;
    char name[100];
    char author[50];
    int count;
};

// 2. 全局变量
struct Book books[1000];
int book_num = 0;
int is_admin = 0;  // 0-普通用户，1-管理员

// 清屏函数（跨平台）
void clear_screen() {
    #ifdef _WIN32
        system("cls");  // Windows系统
    #else
        system("clear");  // Linux/Mac系统
    #endif
}

// 检查编号是否存在
int check_id_exists(int id) {
    int i;
    for(i = 0; i < book_num; i++) {
        if(books[i].id == id) {
            return 1;
        }
    }
    return 0;
}

// 初始化10本图书
void init_books() {
    clear_screen();  // 清屏
    printf("正在初始化图书数据...\n");
    
    // 第一本书
    books[0].id = 1001;
    strcpy(books[0].name, "C语言程序设计");
    strcpy(books[0].author, "谭浩强");
    books[0].count = 5;
    
    // 第二本书
    books[1].id = 1002;
    strcpy(books[1].name, "数据结构");
    strcpy(books[1].author, "严蔚敏");
    books[1].count = 3;
    
    // 第三本书
    books[2].id = 1003;
    strcpy(books[2].name, "计算机组成原理");
    strcpy(books[2].author, "唐朔飞");
    books[2].count = 4;
    
    // 第四本书
    books[3].id = 1004;
    strcpy(books[3].name, "操作系统");
    strcpy(books[3].author, "汤小丹");
    books[3].count = 6;
    
    // 第五本书
    books[4].id = 1005;
    strcpy(books[4].name, "计算机网络");
    strcpy(books[4].author, "谢希仁");
    books[4].count = 2;
    
    // 第六本书
    books[5].id = 1006;
    strcpy(books[5].name, "数据库系统概论");
    strcpy(books[5].author, "王珊");
    books[5].count = 7;
    
    // 第七本书
    books[6].id = 1007;
    strcpy(books[6].name, "高等数学");
    strcpy(books[6].author, "同济大学");
    books[6].count = 10;
    
    // 第八本书
    books[7].id = 1008;
    strcpy(books[7].name, "大学英语");
    strcpy(books[7].author, "李荫华");
    books[7].count = 8;
    
    // 第九本书
    books[8].id = 1009;
    strcpy(books[8].name, "算法导论");
    strcpy(books[8].author, "Thomas H. Cormen");
    books[8].count = 2;
    
    // 第十本书
    books[9].id = 1010;
    strcpy(books[9].name, "编程珠玑");
    strcpy(books[9].author, "Jon Bentley");
    books[9].count = 3;
    
    book_num = 10;
    printf("已初始化10本图书数据！\n");
    
    // 暂停一下，让用户看到初始化信息
    printf("\n按任意键继续...");
    getchar();
}

// 3. 主菜单（根据用户身份显示不同菜单）
void show_menu() {
    clear_screen();  // 清屏
    
    printf("\n===== 图书管理系统 =====\n");
    
    if(is_admin == 1) {
        printf("当前身份：管理员\n");
        printf("1. 添加图书\n");
        printf("2. 查看所有图书\n");
        printf("3. 查找图书\n");
        printf("4. 切换用户\n");
        printf("5. 退出\n");
    } else {
        printf("当前身份：普通用户\n");
        printf("1. 查看所有图书\n");
        printf("2. 查找图书\n");
        printf("3. 切换用户\n");
        printf("4. 退出\n");
    }
    
    printf("请选择: ");
}

// 检查字符串是否只包含数字
int is_number(char* str) {
    int i = 0;
    if(str[0] == '-') {
        i = 1;
    }
    
    while(str[i] != '\0') {
        if(str[i] < '0' || str[i] > '9') {
            return 0;
        }
        i++;
    }
    return 1;
}

// 检查编号是否在1000-2000之间
int check_id_range(int id) {
    if(id >= 1000 && id <= 2000) {
        return 1;
    }
    return 0;
}

// 4. 添加图书（只有管理员可用）
void add_book() {
    clear_screen();  // 清屏
    
    if(is_admin == 0) {
        printf("权限不足！只有管理员可以添加图书。\n");
        printf("\n按任意键返回主菜单...");
        getchar();
        getchar();  // 多一个getchar是因为之前的输入缓冲区可能还有回车
        return;
    }
    
    printf("\n--- 添加新图书 ---\n");
    
    // 检查空间
    if(book_num >= 1000) {
        printf("图书库已满，无法添加新书！\n");
        printf("\n按任意键返回主菜单...");
        getchar();
        return;
    }
    
    int new_id;
    int id_valid;
    int i;
    char input[50];
    
    // 检查编号格式、范围和重复
    for(i = 0; i < 3; i++) {
        printf("请输入图书编号(1000-2000): ");
        scanf("%s", input);
        
        // 检查输入是否为纯数字
        if(is_number(input)) {
            // 将字符串转换为整数
            new_id = 0;
            int j = 0;
            while(input[j] != '\0') {
                new_id = new_id * 10 + (input[j] - '0');
                j++;
            }
            
            // 检查编号范围
            if(!check_id_range(new_id)) {
                printf("错误：编号必须在1000到2000之间！\n");
                id_valid = 0;
            }
            // 检查编号是否已存在
            else if(check_id_exists(new_id)) {
                printf("错误：编号 %d 已存在！\n", new_id);
                id_valid = 0;
            } else {
                id_valid = 1;
                break;
            }
        } else {
            printf("错误：编号必须是数字！请重新输入。\n");
            id_valid = 0;
        }
        
        // 如果输入无效，且还有重试机会
        if(!id_valid && i < 2) {
            printf("请重新输入 (还剩 %d 次机会):\n", 2-i);
        }
    }
    
    // 如果3次尝试都失败
    if(i >= 3 && !id_valid) {
        printf("尝试次数过多，添加操作取消。\n");
        printf("\n按任意键返回主菜单...");
        getchar();
        getchar();
        return;
    }
    
    // 输入其他信息
    books[book_num].id = new_id;
    
    printf("请输入书名: ");
    scanf("%s", books[book_num].name);
    
    printf("请输入作者: ");
    scanf("%s", books[book_num].author);
    
    // 库存数量验证
    int valid_count = 0;
    while(!valid_count) {
        printf("请输入库存数量: ");
        
        // 尝试读取整数
        if(scanf("%d", &books[book_num].count) == 1) {
            // 检查是否为正数
            if(books[book_num].count >= 0) {
                if(books[book_num].count == 0) {
                    printf("警告：库存数量为0，这本书将无法借阅。\n");
                }
                valid_count = 1;
            } else {
                printf("错误：库存数量不能为负数！请重新输入。\n");
            }
        } else {
            // 清除错误的输入
            char ch;
            while((ch = getchar()) != '\n' && ch != EOF);
            printf("错误：库存数量必须是数字！请重新输入。\n");
        }
    }
    
    book_num++;
    printf("\n添加成功！\n");
    printf("\n按任意键返回主菜单...");
    getchar();
    getchar();
}

// 5. 显示所有图书
void show_all() {
    clear_screen();  // 清屏
    
    printf("\n--- 所有图书信息 ---\n");
    
    if(book_num == 0) {
        printf("暂无图书\n");
    } else {
        printf("编号\t书名\t\t作者\t\t库存\n");
        printf("-------------------------------------------\n");
        
        int i;
        for(i = 0; i < book_num; i++) {
            printf("%d\t%-15s\t%-15s\t%d\n", 
                   books[i].id, 
                   books[i].name, 
                   books[i].author, 
                   books[i].count);
        }
    }
    
    printf("\n按任意键返回主菜单...");
    getchar();
    getchar();
}

// 6. 查找图书
void find_book() {
    clear_screen();  // 清屏
    
    int find_id;
    char input[50];
    printf("\n请输入要查找的图书编号(1000-2000): ");
    
    // 读取为字符串并验证是否为数字
    scanf("%s", input);
    
    // 检查输入是否为纯数字
    if(!is_number(input)) {
        printf("错误：编号必须是数字！\n");
        printf("\n按任意键返回主菜单...");
        getchar();
        getchar();
        return;
    }
    
    // 将字符串转换为整数
    find_id = 0;
    int i = 0;
    while(input[i] != '\0') {
        find_id = find_id * 10 + (input[i] - '0');
        i++;
    }
    
    // 检查编号范围
    if(!check_id_range(find_id)) {
        printf("错误：编号必须在1000到2000之间！\n");
        printf("\n按任意键返回主菜单...");
        getchar();
        getchar();
        return;
    }
    
    for(i = 0; i < book_num; i++) {
        if(books[i].id == find_id) {
            printf("\n找到图书：\n");
            printf("编号: %d\n", books[i].id);
            printf("书名: %s\n", books[i].name);
            printf("作者: %s\n", books[i].author);
            printf("库存: %d\n", books[i].count);
            printf("\n按任意键返回主菜单...");
            getchar();
            getchar();
            return;
        }
    }
    
    printf("未找到编号为%d的图书\n", find_id);
    printf("\n按任意键返回主菜单...");
    getchar();
    getchar();
}

// 7. 切换用户身份
void switch_user() {
    clear_screen();  // 清屏
    
    char input[10];
    int choice;
    
    printf("\n--- 切换用户身份 ---\n");
    printf("1. 普通用户\n");
    printf("2. 管理员\n");
    printf("请选择身份: ");
    
    scanf("%s", input);
    
    // 检查输入是否为纯数字
    if(!is_number(input)) {
        printf("输入错误，请输入数字！\n");
        printf("\n按任意键返回主菜单...");
        getchar();
        getchar();
        return;
    }
    
    // 将字符串转换为整数
    choice = 0;
    int i = 0;
    while(input[i] != '\0') {
        choice = choice * 10 + (input[i] - '0');
        i++;
    }
    
    if(choice == 1) {
        is_admin = 0;
        printf("已切换到普通用户身份\n");
    } else if(choice == 2) {
        is_admin = 1;
        printf("已切换到管理员身份\n");
    } else {
        printf("选择错误！\n");
    }
    
    printf("\n按任意键返回主菜单...");
    getchar();
    getchar();
}

// 8. 主函数
int main() {
    clear_screen();  // 程序开始时清屏
    
    int choice;
    char input[10];
    
    printf("欢迎使用图书管理系统！\n");
    printf("注意：图书编号必须在1000-2000之间\n");
    
    // 初始化身份选择
    printf("\n--- 请选择初始身份 ---\n");
    printf("1. 普通用户\n");
    printf("2. 管理员\n");
    printf("请选择: ");
    
    scanf("%s", input);
    
    // 检查输入是否为纯数字
    if(!is_number(input)) {
        printf("输入错误，默认设为普通用户\n");
        is_admin = 0;
    } else {
        // 将字符串转换为整数
        choice = 0;
        int i = 0;
        while(input[i] != '\0') {
            choice = choice * 10 + (input[i] - '0');
            i++;
        }
        
        if(choice == 2) {
            is_admin = 1;
            printf("您选择了管理员身份\n");
        } else {
            is_admin = 0;
            printf("您选择了普通用户身份\n");
        }
    }
    
    printf("\n按任意键继续...");
    getchar();
    getchar();
    
    // 初始化图书数据
    init_books();
    
    while(1) {
        show_menu();
        
        // 读取菜单选择并验证
        scanf("%s", input);
        
        // 检查输入是否为纯数字
        if(is_number(input)) {
            // 将字符串转换为整数
            choice = 0;
            int i = 0;
            while(input[i] != '\0') {
                choice = choice * 10 + (input[i] - '0');
                i++;
            }
            
            // 根据用户身份处理不同菜单选项
            if(is_admin == 1) {
                // 管理员菜单选项
                switch(choice) {
                    case 1:
                        add_book();
                        break;
                    case 2:
                        show_all();
                        break;
                    case 3:
                        find_book();
                        break;
                    case 4:
                        switch_user();
                        break;
                    case 5:
                        clear_screen();
                        printf("谢谢使用，再见！\n");
                        return 0;
                    default:
                        printf("输入错误，请重新选择！\n");
                        printf("\n按任意键继续...");
                        getchar();
                        getchar();
                }
            } else {
                // 普通用户菜单选项
                switch(choice) {
                    case 1:
                        show_all();
                        break;
                    case 2:
                        find_book();
                        break;
                    case 3:
                        switch_user();
                        break;
                    case 4:
                        clear_screen();
                        printf("谢谢使用，再见！\n");
                        return 0;
                    default:
                        printf("输入错误，请重新选择！\n");
                        printf("\n按任意键继续...");
                        getchar();
                        getchar();
                }
            }
        } else {
            printf("输入错误，请输入数字！\n");
            printf("\n按任意键继续...");
            getchar();
            getchar();
        }
    }
    
    return 0;
}
