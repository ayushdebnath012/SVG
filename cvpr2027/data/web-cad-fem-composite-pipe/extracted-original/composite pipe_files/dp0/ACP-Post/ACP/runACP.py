# -*- coding: utf-8 -*-
import compolyx
db = compolyx.DB()
db.open( path=u'E:\\Fiver\\Composite Pipe\\composite pipe_files\\dp0\\ACP-Post\\ACP\\ACP-Post.acp', replace_workbench_inputs={'open':{'path':u'E:\\Fiver\\Composite Pipe\\composite pipe_files\\dp0\\ACP-Post\\ACP\\ACP-Pre.acp'}, 'import_model':{'path':u'E:\\Fiver\\Composite Pipe\\composite pipe_files\\dp0\\ACP-Post\\ACP\\ACP-Pre-1.1.h5'}, 'import_matml':{'path':u'E:\\Fiver\\Composite Pipe\\composite pipe_files\\dp0\\ACP-Post\\ACP\\material.engd', 'material_apdl_path':u'E:\\Fiver\\Composite Pipe\\composite pipe_files\\dp0\\ACP-Post\\ACP\\material.apdl'}, 'add_solutions':[{'name':'Solution 1', 'ext_id':'Solution', 'path':u'E:\\Fiver\\Composite Pipe\\composite pipe_files\\dp0\\SYS\\MECH\\file.rst'},], })
