#include <bits/stdc++.h>

using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, sum = 0;
    cin >> n;

    while (n--) {
        string a;
        cin >> a;
        if (a == "Tetrahedron") sum += 4;
        else if (a == "Cube") sum += 6;
        else if (a == "Octahedron") sum += 8;
        else if (a == "Dodecahedron") sum += 12;
        else if (a == "Icosahedron") sum += 20;
    }

    cout << sum << endl;

    return 0;
}
