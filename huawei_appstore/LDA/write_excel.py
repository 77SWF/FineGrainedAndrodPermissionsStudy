import xlwt
import xlrd
from xlutils.copy import copy

class My_xlwt(object):
    def __init__(self,sheet_name = 'sheet_1',re_write = True):
        '''
        自定义类说明：
        :param sheet_name:默认sheet表对象名称，默认值为 'sheet_1'
        :param re_write: 单元格重写写功能默认开启
        '''
        self.work_book = xlwt.Workbook()
        self.sheet = self.work_book.add_sheet(sheet_name,
                                cell_overwrite_ok=re_write)
        self.col_data = {}
        
    def save(self,file_name):
        self.work_book.save(file_name)

    def write(self,row,col,label):
        '''
        在默认sheet表对象一个单元格内写入数据
        :param row: 写入行
        :param col: 写入列
        :param label: 写入数据
        '''
        self.sheet.write(row,col,label)
        
        # 将列数据加入到col_data字典中
        if col not in self.col_data.keys():
            self.col_data[col] = []
            self.col_data[col].append(label)
        else:
            self.col_data[col].append(label)

    def write_row(self,start_row,start_col,date_list):
        '''
        按行写入一行数据
        :param start_row:写入行序号
        :param start_col: 写入列序号
        :param date_list: 写入数据：列表
        :return: 返回行对象
        '''
        for col,label in enumerate(date_list):
            self.write(start_row,start_col+col,label)

        return self.sheet.row(start_row)

    def write_col(self,start_row,start_col,date_list):
        '''
        按列写入一列数据
        :param start_row:写入行序号
        :param start_col: 写入列序号
        :param date_list: 写入数据：列表
        :return: 返回写入的列对象
        '''
        for row,label in enumerate(date_list):
            self.write(row+start_row,start_col,label)

        return self.sheet.col(start_col)


#追加写入xls
def write_excel_xls_append(path, id_sheet,value):
    index = len(value)  # 获取需要写入数据的行数

    workbook = xlrd.open_workbook(path)  # 打开工作簿
    sheets = workbook.sheet_names()  # 获取工作簿中的所有表格
    worksheet = workbook.sheet_by_name(sheets[id_sheet])  # 获取工作簿中所有表格中的的第一个表格

    rows_old = worksheet.nrows  # 获取表格中已存在的数据的行数
    cols_old = worksheet.ncols  # 获取表格中已存在的数据的行数

    new_workbook = copy(workbook)  # 将xlrd对象拷贝转化为xlwt对象
    new_worksheet = new_workbook.get_sheet(id_sheet)  # 获取转化后工作簿中的第一个表格

    for i in range(0, index):
        for j in range(0, len(value[i])):
            new_worksheet.write(i, j+cols_old, value[i][j])  # 追加写入数据，注意是从i+rows_old行开始写入
    new_workbook.save(path)  # 保存工作簿
    print("xls格式表格【追加】写入数据成功！")



import xlrd
import xlutils.copy as xc

def write_excel_xls_append(path, id_sheet,value):
    index = len(value)  # 获取需要写入数据的行数

    workbook = xlrd.open_workbook(path)  # 打开工作簿
    sheets = workbook.sheet_names()  # 获取工作簿中的所有表格
    worksheet = workbook.sheet_by_name(sheets[id_sheet])  # 获取工作簿中所有表格中的的第一个表格

    rows_old = worksheet.nrows  # 获取表格中已存在的数据的行数
    cols_old = worksheet.ncols  # 获取表格中已存在的数据的行数

    new_workbook = xc.copy(workbook)  # 将xlrd对象拷贝转化为xlwt对象
    new_worksheet = new_workbook.get_sheet(id_sheet)  # 获取转化后工作簿中的第一个表格

    for i in range(0, index):
        for j in range(0, len(value[i])):
            new_worksheet.write(i, j+cols_old, str(value[i][j]))  # 追加写入数据，注意是从i+rows_old行开始写入
    new_workbook.save(path)  # 保存工作簿
    print("写入完成！")



if __name__ == '__main__':
    data = [[1,2],[3,4],[5,6,7]]
    write_excel_xls_append("my_test.xls",0,data)