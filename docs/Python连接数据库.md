# Python连接数据库
## 安装
推荐用`sqlalchemy`可以适配不同数据库，安装`pip install sqlalchemy`

## 使用
比如使用PostgreSQL数据库，这里第一次运行可能会提示找不到连接库，需要看看命令行检查缺什么库再安装
### 连接数据库
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 引擎
engine = create_engine('postgresql://postgres:123.com@localhost:5432/test')
# 会话创建器
Session = sessionmaker(bind=engine)
```

### 查询
```python
with Session() as session:
    result = session.execute(text("SELECT * FROM public.user;"))
    for row in result:
        print(row)
```

### 带WHERE查询
注意要避免SQL注入
```python
from sqlalchemy import text
stmt = text("SELECT * FROM public.user WHERE id=:id")
with Session() as session:
    result = session.execute(stmt, {"id": 1})
    for row in result:
        print(row)
```
此处text必须带，用于告诉sqlalchemy这是个SQL语句

## ORM
ORM是Object-Relational Mapping的缩写，即对象关系映射，是一种将数据库中的数据映射到对象中的技术。

### 定义一个表
```python
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    # __table_args__ = {"schema": "public"} 默认
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    score = Column(Integer)
```

### 创建表
个人开发中可以直接用`Base.metadata.create_all(engine)`创建表，
但实际生产中应该用`alembic`库创建，甚至应该手动建表

### 查询
可以用专门的语句编写查询语句
```python
from sqlalchemy import select

with Session() as session:
    stmt = select(User).where(User.id == 1)
    result = session.execute(stmt)
    print(result.scalars().one())
```
result是一个类似于表的对象，由于select里只有一个User参数，所以结果中只有一列，
而scalars用于获取第一列，one获取第一行（如果有多行会报错），最后就是获取一个唯一的User对象  
scalar()等于scalars().first()

### 插入
```python
user = User(name='张三', score=80)
with Session() as session:
    session.add(user)
    print(user.id)
    session.flush([user])
    print(user.id)
    session.commit()
```
这里输出None和5，因为add后并没有立即插入数据库，而是先保存到session中，需要手动flush  
flush会同步数据库，将自增ID写进对象，最后的commit就是事务的提交函数，正式更改数据库

再看下一个例子
```python
user = User(name='张三', score=80)
with Session() as session:
    session.add(user)
    print(user.id)
    session.execute(select(User).where(User.name == user.name))
    print(user.id)
```
这里同样输出None和5，因为`sessionmaker`有一个autoflush参数，默认为True，在查询前会自动flush  
所以如果设置`sessionmaker(bind=engine, autoflush=False)`，这里就会输出两个None

## 异步会话
使用异步需要修改SQL URL，可以看下面示例，运行时需要安装`asyncpg`
```python
import asyncio

from sqlalchemy import Column, String, Integer, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    score = Column(Integer)


engine = create_async_engine('postgresql+asyncpg://postgres:123.com@localhost:5432/test')
Session = async_sessionmaker(bind=engine)


async def main():
    async with engine.begin() as conn:  # 自动创建连接，退出时自动提交
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as session:
        result = await session.execute(select(User))
        for scalar in result.scalars():
            print(scalar.name, scalar.score)
    await engine.dispose()


asyncio.run(main())
```