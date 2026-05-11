#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
using namespace std;

class Student {
public:
    string id;
    string name;
    int prog;   // 程序设计成绩
    int net;    // 网络成绩
    int db;     // 数据库成绩

    Student(string id, string name, int prog, int net, int db)
        : id(id), name(name), prog(prog), net(net), db(db) {}

    // 计算总分
    int totalScore() const {
        return prog + net + db;
    }

    // 计算平均分
    double averageScore() const {
        return totalScore() / 3.0;
    }

    void display() const {
        cout << id << "\t" << name << "\t"
             << prog << "\t" << net << "\t" << db << "\t"
             << totalScore() << "\t" << averageScore() << endl;
    }
};

class StudentInfo {
private:
    vector<Student> students;

public:
    void addStudent(const Student& s) {
        students.push_back(s);
    }

    // 按总分降序排名并显示
    void displayRanking() {
        vector<Student> sorted = students;
        sort(sorted.begin(), sorted.end(), [](const Student& a, const Student& b) {
            return a.totalScore() > b.totalScore();
        });

        cout << "\n===== 成绩排名（按总分降序）=====" << endl;
        cout << "排名\t学号\t姓名\t程序设计\t网络\t数据库\t总分\t平均分" << endl;
        int rank = 1;
        for (const auto& s : sorted) {
            cout << rank++ << "\t";
            s.display();
        }
    }

    // 显示平均分高于 threshold 的学生
    void displayHighScorers(double threshold = 85) {
        cout << "\n===== 平均分高于 " << threshold << " 的学生 =====" << endl;
        cout << "学号\t姓名\t程序设计\t网络\t数据库\t总分\t平均分" << endl;
        bool found = false;
        for (const auto& s : students) {
            if (s.averageScore() > threshold) {
                s.display();
                found = true;
            }
        }
        if (!found) {
            cout << "无" << endl;
        }
    }
};

int main() {
    StudentInfo info;

    // 添加学生数据
    info.addStudent(Student("2024001", "张三", 90, 85, 88));
    info.addStudent(Student("2024002", "李四", 78, 92, 80));
    info.addStudent(Student("2024003", "王五", 95, 88, 91));

    info.displayRanking();
    info.displayHighScorers(85);

    return 0;
}
