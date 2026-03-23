CXX := g++
CXXFLAGS := -std=c++20 -O2 -Wall -Wextra -pthread -Iinclude
TARGET := benchmark
SRC := BenchmarkSecurity.cpp

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRC)

clean:
	rm -f $(TARGET)