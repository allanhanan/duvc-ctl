#pragma once

/**
 * @file com_helpers.h
 * @brief Internal COM utility classes and functions
 * 
 * @internal This header contains implementation details and should not be used directly.
 */

#ifdef _WIN32

#include <windows.h>
#include <combaseapi.h>
#include <stdexcept>
#include <string>

namespace duvc::detail {

/**
 * @brief Smart pointer for COM interfaces
 * @tparam T COM interface type
 * 
 * @internal RAII wrapper for COM interface pointers with proper reference counting.
 */
template<typename T>
class com_ptr {
public:
    /// Default constructor
    com_ptr() noexcept = default;
    
    /**
     * @brief Construct from raw pointer (takes ownership)
     * @param p Raw interface pointer
     */
    explicit com_ptr(T* p) noexcept : p_(p) {}
    
    /// Destructor - releases interface
    ~com_ptr() { reset(); }
    
    // Non-copyable
    com_ptr(const com_ptr&) = delete;
    com_ptr& operator=(const com_ptr&) = delete;
    
    /// Move constructor
    com_ptr(com_ptr&& o) noexcept : p_(o.p_) { o.p_ = nullptr; }
    
    /// Move assignment
    com_ptr& operator=(com_ptr&& o) noexcept {
        if (this != &o) { 
            reset(); 
            p_ = o.p_; 
            o.p_ = nullptr; 
        }
        return *this;
    }
    
    /// Get raw pointer
    T* get() const noexcept { return p_; }
    
    /// Get address for output (releases current)
    T** put() noexcept { reset(); return &p_; }
    
    /// Pointer access
    T* operator->() const noexcept { return p_; }
    
    /// Boolean conversion
    explicit operator bool() const noexcept { return p_ != nullptr; }
    
    /// Release current interface
    void reset() noexcept { 
        if (p_) { 
            p_->Release(); 
            p_ = nullptr; 
        } 
    }

private:
    T* p_ = nullptr;
};

/**
 * @brief COM apartment management
 * 
 * @internal Ensures proper COM initialization/cleanup for device operations.
 */
class com_apartment {
public:
    /// Initialize COM apartment
    com_apartment();
    
    /// Cleanup COM apartment
    ~com_apartment();
    
    // Non-copyable, non-movable
    com_apartment(const com_apartment&) = delete;
    com_apartment& operator=(const com_apartment&) = delete;
    com_apartment(com_apartment&&) = delete;
    com_apartment& operator=(com_apartment&&) = delete;

private:
    HRESULT hr_;
};

/**
 * @brief Convert wide string to UTF-8
 * @param ws Wide string input
 * @return UTF-8 encoded string
 * 
 * @internal Utility for error message conversion.
 */
std::string wide_to_utf8(const wchar_t* ws);

/**
 * @brief Throw exception with HRESULT information
 * @param hr Failed HRESULT
 * @param where Description of operation that failed
 * @throws std::runtime_error with formatted error message
 * 
 * @internal Helper for consistent error reporting.
 */
void throw_hr(HRESULT hr, const char* where);

} // namespace duvc::detail

#endif // _WIN32
