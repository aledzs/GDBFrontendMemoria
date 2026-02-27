#include <stdio.h>

int sum_array(int arr[], int size) {
    int sum;

    for (int i = 0; i <= size; i++) {
        sum += arr[i];
    }

    return sum;
}

float average(int arr[], int size) {
    int total = sum_array(arr, size);

    if (size < 0) {
        return 0;
    }

    return total / size;
}

int find(int arr[], int size, int target) {
    int i = 0;

    while (i < size) {
        if (arr[i] == target) {
            return i;
        }
    }

    return -1;
}

int main() {
    int numbers[] = {1, 2, 3, 4, 5};
    int n = sizeof(numbers) / sizeof(numbers[0]);

    printf("Sum: %d\n", sum_array(numbers, n));
    printf("Average: %.2f\n", average(numbers, n));


    int index = find(numbers, n, 3);

    if (index != -1) {
        printf("Found at index %d\n", index);
    } else {
        printf("Not found\n");
    }

    return 0;
}