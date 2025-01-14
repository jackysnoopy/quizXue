#!/usr/bin/env python
# -*- coding:utf-8 -*-
'''
@file: model.py
@author: kessil
@contact: https://github.com/kessil/
@time: 2019年06月02日 15:57:45
@desc: Life is short, you need Python
'''
from sqlalchemy import Column,Integer, String, Text, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config import Config
import re
from lxml import etree

# 创建对象的基类:
Base = declarative_base()

# 定义Bank对象:
class Bank(Base):
    # 表的名字:
    __tablename__ = 'Bank'

    # 表的结构:
    id = Column(Integer,primary_key=True)
    content = Column(Text, unique=True)
    item1 = Column(String(128))
    item2 = Column(String(128))
    item3 = Column(String(128))
    item4 = Column(String(128))
    answer = Column(String(8))
    bounds = Column(String(64))

    def __init__(self, content, options, answer='', bounds=''):
        for i in range(len(options), 4):
            options.append('')
        # print(options)
        self.content = content
        self.item1, self.item2, self.item3, self.item4 = [str(x) for x in options]
        self.answer = answer
        self.bounds = bounds

    @classmethod
    def from_xml(cls, filename):
        xml = etree.parse(filename)
        root = xml.getroot()
        xml_question = root.xpath(Config.XPATH_QUESTION)[0]
        content = xml_question.xpath(Config.XPATH_CONTENT)[0]
        xml_options = xml_question.xpath(Config.XPATH_OPTIONS)
        options = [x.xpath(Config.XPATH_OPTOIN_DESC)[0] for x in xml_options]
        bounds = []
        for x in xml_options:
            ''' 此处保存的bounds针对华为P20 分辨率2244*1080'''
            x0, y0, x1, y1 = [int(x) for x in re.findall(r'\d+', x.xpath(Config.XPATH_OPTION_BOUNDES)[0])]
            pos = complex((x0+x1)/2, (y0+y1)/2)
            bounds.append(pos)
        bounds = " ".join([str(x) for x in bounds])
        # print(bounds)
        return cls(content=content, options=options, bounds=bounds)

    def __eq__(self, other):
        # if self.content != other.content:
        #     return False
        # if self.item1 != other.item1:
        #     return False
        # if self.item2 != other.item2:
        #     return False
        # if self.item3 != other.item3:
        #     return False
        # if self.item4 != other.item4:
        #     return False
        # return True
        return self.content == other.content
    
    def __repr__(self):
        return f'{self.content}\n'
    
    def __str__(self): 
        # 统一题目内容的留空为两个英文下划线
        # 江南自古富庶地，风流才子美名扬，江南四大才子是__、__、__、__。 
        # 油锅起火时使用以下方法中__方法扑灭是不正确的。
        content = re.sub(r'[\(（]出题单位.*', "", self.content)
        content = re.sub(r'(\s{2,})|(（\s*）)|(【\s*】)', '____', content)
        items = [x for x in (self.item1, self.item2, self.item3, self.item4) if x]
        index = ord(self.answer)-65
        if index < len(items):
            items[index] = f'**{items[index]}**'
        options = '\n'.join([f'+ {x}' for x in items])
        return f'{self.id}. {content} **{self.answer.upper()}**\n{options}\n'
    

# 初始化数据库连接:
engine = create_engine(Config.DATABASE_URI)

# 创建DBSession类型:
Session = sessionmaker(bind=engine)

def db_add(session, item):
    '''数据库添加纪录'''
    result = session.query(Bank).filter_by(content=item.content).first()
    if result:
        print('数据库已存在此纪录')
    else:
        session.add(item)
        session.commit()
        print('数据库添加记录成功！')

def db_update(session, id, answer):
    to_update = db_qeury(session, id=id)
    to_update.answer = answer
    session.commit()
    print(f'更新题目[{id}]的答案为“{answer}”')


def db_qeury(session, id=None, content=None):
    '''数据库检索记录'''
    if id and isinstance(id, int):
        return session.query(Bank).filter_by(id=id).first()
    if content and isinstance(content, str):
        return session.query(Bank).filter_by(content=content).first()
    return session.query(Bank).all()

def db_delete(session, item):
    '''数据库删除记录'''
    to_del = db_qeury(session, content=item.content)
    session.delete(to_del)
    session.commit()

def db_print(session):
    data = db_qeury(session)
    print(f'学习强国题库: {len(data)} 题\n')
    for d in data:
        print(d)

def db_to_xls(session, filename):
    import xlwt
    data = session.query(Bank).all()
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('题库')
    if not data:
        raise 'database is empty'
    ws.write(0, 0, '序号')
    ws.write(0, 1, '题目')
    ws.write(0, 2, '选项A')
    ws.write(0, 3, '选项B')
    ws.write(0, 4, '选项C')
    ws.write(0, 5, '选项D')
    ws.write(0, 6, '答案')
    for d in data:
        ws.write(d.id, 0, label=d.id)
        ws.write(d.id, 1, label=re.sub(r'\s+', '', d.content))
        ws.write(d.id, 2, label=d.item1)
        ws.write(d.id, 3, label=d.item2)
        ws.write(d.id, 4, label=d.item3)
        ws.write(d.id, 5, label=d.item4)
        ws.write(d.id, 6, label=d.answer)
    wb.save(filename)
    print('题库已导出到%s'%filename)

def db_to_mtb(session, filename):
    '''导出到磨题帮题库模板'''
    import xlwt
    data = session.query(Bank).all()
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('题库')
    if not data:
        raise 'database is empty'
    ws.write(0, 0, label='标题')
    ws.write_merge(0,0,1,7,"学习强国一战到底")
    ws.write(1, 0, label='描述')
    ws.write_merge(1,1,1,7,"一份学习强国挑战答题试卷，全为单选题")
    ws.write(2, 0, label='用时')
    ws.write(2, 1, 100)
    ws.write(3, 0, label='题干')
    ws.write(3, 1, label='题型')
    ws.write(3, 2, label='选择项1')
    ws.write(3, 3, label='选择项2')
    ws.write(3, 4, label='选择项3')
    ws.write(3, 5, label='选择项4')
    ws.write(3, 6, label='解析')
    ws.write(3, 7, label='答案')
    ws.write(3, 8, label='得分')
    for d in data:
        row = d.id + 3
        ws.write(row, 0, label=d.content)
        ws.write(row, 1, label='顺序选择题')
        ws.write(row, 2, label=d.item1)
        ws.write(row, 3, label=d.item2)
        ws.write(row, 4, label=d.item3)
        ws.write(row, 5, label=d.item4)
        ws.write(row, 6, label='')
        ws.write(row, 7, label=d.answer)
        ws.write(row, 8, 1)
    wb.save(filename)
    print('题库(磨题帮)已导出到%s'%filename)


def db_from_xls(session, filename):
    import xlrd
    wb = xlrd.open_workbook(filename)
    ws = wb.sheet_by_index(0)
    nrows = ws.nrows  #获取该sheet中的有效行数
    if nrows < 2:
        raise 'Excel has no records'
    for i in range(1, nrows):
        bank = Bank(content=ws.cell_value(i, 1), 
                    options=ws.row_values(i, start_colx=2, end_colx=6), 
                    answer=ws.cell_value(i, 6))
        db_add(session, bank)
    print('更新数据库成功！来源：%s %d'%(filename, len(data)))



def db_to_md(session, filename):
    data = session.query(Bank).all()
    if not data:
        raise 'database is empty'
    with open(filename, 'w', encoding='utf-8') as fp:
        fp.write(f'# 学习强国题库： {len(data)} 题\n')
        for d in data:
            fp.write(str(d))

    print('题库已导出到%s'%filename)
    
    
def main():
    # 创建数据表
    Base.metadata.create_all(engine)
    session = Session()

    while True:
        print('%s\n%s\n%s'%('-*-'*28, '\tp-打印题库\tu-更新记录\tx-导出xls\tm-导出md\te-退出', '-*-'*28))
        ch = input('''请输入：''').upper()
        if 'E' == ch:
            break
        elif 'P' == ch:
            db_print(session)
        elif 'U' == ch:
            print('暂不支持此功能')
            # # 暂不支持此功能
            # s = input('请在一行输入题目序号和修正的答案，空格隔开。请输入：')
            # idx, new_ans = s.split(" ")
            # print(db_qeury(session, id=int(idx)))
            # ok = input(f'修改答案为: {new_ans} 确认？(输入 N 撤销)').upper()
            # if 'N' != ok: db_update(session, int(idx), new_ans.upper())
        elif 'X' == ch:
            db_to_xls(session, './data/data-dev.xls')
            db_to_mtb(session, './data/data-mtb.xls')
        elif 'M' == ch:
            db_to_md(session, './data/data-dev.md')
        else:
            print('输入错误，请重新输入！')


if __name__ == "__main__":
    

    main()

    # 执行操作
    # bank = Bank(content='近期，我国学者研究“多节点网络”取得基础性突破。（出题单位：科技部引智司）',
    #             options=['电子', '原子', '质子', '量子'], answer='D')
    # db_add(session, bank)
    # db_print(session)

    # xls 导入
    # filename = "C:/Users/vince/repositories/quizXue/data/data-dev-old.xls"
    # db_from_xls(session, filename)
    
    # bank = Bank.from_xml('./ui.xml')

