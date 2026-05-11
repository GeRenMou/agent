#include <iostream>
using namespace std;

class Complex {
private:
    double real;
    double imag;

public:
    Complex(double r, double i) : real(r), imag(i) {}

    double getReal() const {
        return real;
    }

    double getImag() const {
        return imag;
    }

    static Complex add(const Complex& c1, const Complex& c2) {
        return Complex(c1.real + c2.real, c1.imag + c2.imag);
    }

    void display() const {
        cout << real;
        if (imag >= 0) {
            cout << " + " << imag << "i";
        } else {
            cout << " - " << -imag << "i";
        }
        cout << endl;
    }
};

int main() {
    Complex c1(3.0, 4.0);
    Complex c2(1.5, -2.5);

    cout << "c1 = "; c1.display();
    cout << "c2 = "; c2.display();

    Complex c3 = Complex::add(c1, c2);
    cout << "c1 + c2 = "; c3.display();

    return 0;
}
