# **Authentication in Ellar** 

Authentication is an essential part of most applications. It verifies the identity of users interacting with your application. Ellar provides flexible and powerful authentication mechanisms to suit different application needs.

## **Overview**

Ellar offers two main approaches to authentication:

1. **Guard Strategy** - Authentication performed at the route handler level
2. **Authentication Handler Strategy** - Authentication performed at the middleware layer

### **When to Use Each Strategy**

1. #### **Guard Strategy**:
    - When you need fine-grained control over authentication at the route level
    - When authentication logic varies between different routes
    - When you want to combine multiple authentication methods

2. #### **Authentication Handler Strategy**:
    - When you want consistent authentication across your application
    - When authentication should happen early in the request pipeline
    - When you need to integrate with existing authentication middleware

## **Available Authentication Methods**

Ellar supports various authentication methods out of the box:

- JWT Authentication
- HTTP Basic Authentication
- HTTP Bearer Authentication
- API Key Authentication (Header, Query, Cookie)
- Custom Authentication Schemes

## **Getting Started**

Choose the authentication strategy that best fits your needs:

- [Guard-based Authentication](./guard-strategy.md) - Learn how to implement authentication using Guards
- [Authentication Handler Strategy](./auth-handler-strategy.md) - Implement authentication at the middleware level
- [JWT Authentication Example](./jwt-authentication.md) - Complete example of JWT authentication
- [API Key Authentication](./api-key-authentication.md) - Implement API key-based authentication

## **Best Practices**

1. **Security First**:
    - Never store passwords in plain text
    - Use secure token generation and validation
    - Implement proper error handling

2. **Performance**:
    - Choose the appropriate authentication layer
    - Implement caching where appropriate
    - Consider token expiration strategies

3. **User Experience**:
    - Implement proper token refresh mechanisms
    - Provide clear error messages
    - Consider rate limiting

4. **Code Organization**:
    - Separate authentication logic from business logic
    - Use dependency injection for services
    - Follow Ellar's module structure

## **Next Steps**

Start with the authentication strategy that best matches your requirements:

- For route-level authentication control, begin with [Guard Strategy](./guard-strategy.md)
- For application-wide authentication, check out [Authentication Handler Strategy](./auth-handler-strategy.md) 
