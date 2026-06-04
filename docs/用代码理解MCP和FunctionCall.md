# 用代码理解MCP和function call
最近我写了一个AI库[axi-easyagent](https://github.com/xkgt/axi-easyagent)，从底层了解了一遍MCP和FunctionCall，
这次就通过来学习这个库的方式了解一下这两者
## 1. 先吐个槽
MCP，Skills这几个概念刚出来时，网上一堆吹嘘MCP多牛，Skills多牛，各大厂都推出了自家的MCP的视频和文章，疯狂占据我的首页，还都有几万的播放量，但没一个讲明白原理的，
仿佛在MCP，Skills出现之前，AI就是个智障，只能陪你聊天。

## 2. function call
大语言模型底层就是输入文本输出文本，能调工具完全就是程序告诉模型一个函数名，然后模型输出一个格式，交给程序解析后，调用函数，发起一个新的请求（包含函数结果），这就是function call的底层机制

另外，function call现在被称作tool call，也就是把函数改成了工具

大部分库都会直接封装这个能力，因为他的实现逻辑非常固定，没什么可以改的地方。  
举个例子：使用axi-easyagent的tool call功能
```python
# 通过pip install axi-easyagent安装我写的库
from easyagent import Agent

def get_weather(city: str) -> str:
    """获取城市天气"""
    return f"{city}的天气是晴天"

agent = Agent(model="gpt-3.5-turbo", tools=[get_weather])  # 底层封装，自动执行

async for output in agent.chat("北京天气如何"):
    print(output)  # AI会回答是晴天
```
如果想知道底层是如何轮询的，可以直接看源码

## 3. MCP
你的程序可以写好一大堆函数供AI使用，那么如果要扩展呢，比如打包成执行文件后突然又要加一个新函数怎么办？  

像上面代码，`tools=[get_weather]`是写死的，如果要动态扩展，你的程序可能要实现一个插件功能，每个插件往这个列表插一个新的函数。

又或者开一个新程序，支持RPC调用，只要连接到这个新程序，并把它开放出来的函数注册到tools中，模型调用这个函数时，程序内部用另一个程序的函数，就实现了可扩展性。

这就是MCP的作用，他已经定好了这个规范，只需要所有应用程序，扩展程序遵循这个规范，就能相互调用

### 3.1 吐槽
MCP的目的是挺好的，类似于统一USB接口，但是我手动实现过MCP协议后，觉得他的规范是真垃圾。

### 3.2 用代码使用MCP
```python
from easyagent import MCPSession
# MCP支持进程通信和HTTP通信，所以有两种写法，此处展示进程写法（其实有三种，还有个被废弃的sse通信）
file_system = MCPSession.stdio("npx -y @modelcontextprotocol/server-filesystem .")

async with file_system:
    # list_tools返回列表，里面是构造好的RPC函数
    tools = await file_system.list_tools()
    tools.append(get_weather)  # 再加个内置函数
    from easyagent import Agent
    agent = Agent(model="gpt-3.5-turbo", tools=tools)
    
    async for output in agent.chat("执行rm -rf /"):
        print(output)  # AI回帮你删库跑路
```

## 4. 总结
可以看到两者的关系完全不是一个层级的，没有什么谁可以替代谁是说法（好像在说苹果树可以替代苹果一样）  
function call定义了大语言模型如何调用程序提供的函数，mcp规范了程序如何发现外部提供的函数（这意味着你甚至不需要AI也能执行MCP服务器提供的工具）