#include<iostream>
#include<string>
using namespace std;
int main() {
    std::string a;
    int pos, len;
    getline(cin, a);
    cin >> pos >> len;
    cout << a.substr(pos - 1, len);

    return 0;
}
