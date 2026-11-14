"""Reclassify previously inspected ND13 run as development data and author a fresh holdout."""
import json, shutil
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.common import load, save, sha256, utc


def answer_case(id, question, answer, page, quote, *, kind='direct', filter=None):
    return {'id':id,'split':'test','question':question,'filter':filter or {},'answerable':True,
      'expected_answer':answer,'gold':[{'source_id':'nd13','page':page,'evidence':quote}],
      'absence_reason':None,'kind':kind}


def missing_case(id, question, reason, audit_terms):
    return {'id':id,'split':'dev','question':question,'filter':{},'answerable':False,
      'absence_reason':reason,'absence_audit_terms':audit_terms}


def main():
    old_cases=load('benchmark/nd13/test.json')
    if len(old_cases)!=20: raise ValueError('Expected the frozen 20-case ND13 v1 test')
    old_result=Path('results/nd13/external_v1')
    if not old_result.exists():
        shutil.copytree('results/nd13/test',old_result)
    old_benchmark=Path('benchmark/nd13/external_v1.json')
    if not old_benchmark.exists(): shutil.copy2('benchmark/nd13/test.json',old_benchmark)
    for method in ('baseline','lexical','hybrid','mmr','rerank'):
        rows=load(old_result/method/'traces.json')
        if len(rows)!=20: raise ValueError(f'Incomplete archived external run: {method}')

    dev=[{**q,'split':'dev'} for q in old_cases]
    dev += [
      missing_case('nd13-dev-missing-01',
        'Theo Nghị định 13, mức tiền phạt cụ thể bằng đồng cho hành vi xử lý dữ liệu cá nhân trái pháp luật là bao nhiêu?',
        'Văn bản nêu các hình thức xử lý vi phạm theo pháp luật nhưng không ấn định mức tiền phạt cụ thể bằng đồng.',
        ['mức phạt','phạt tiền','triệu đồng','tỷ đồng','xử phạt vi phạm hành chính']),
      missing_case('nd13-dev-missing-02',
        'Nghị định quy định tối thiểu chính xác bao nhiêu nhân viên phải được chỉ định trong bộ phận bảo vệ dữ liệu cá nhân?',
        'Văn bản yêu cầu chỉ định bộ phận và nhân sự phụ trách nhưng không nêu số lượng nhân viên tối thiểu.',
        ['tối thiểu','số lượng nhân sự','nhân viên bảo vệ dữ liệu','chỉ định bộ phận','chỉ định nhân sự']),
    ]
    test=[
      answer_case('nd13-21',
        'Trong Chương II, khi chủ thể phản đối xử lý dữ liệu để ngăn tiết lộ hoặc dùng cho quảng cáo, tiếp thị, bên kiểm soát phải thực hiện yêu cầu trong bao lâu?',
        'Trong 72 giờ sau khi nhận được yêu cầu, trừ trường hợp luật có quy định khác.',8,
        'Bên Kiểm soát dữ liệu cá nhân, Bên Kiểm soát và xử lý dữ liệu cá nhân thực hiện yêu cầu của chủ thê dữ liệu trong 72 giờ sau khi nhận được yêu cầu, trừ trường hợp luật có quy định khác.',
        kind='condition',filter={'chapter':'II'}),
      answer_case('nd13-22',
        'Sau khi đã thông báo hậu quả và nhận yêu cầu rút lại đồng ý, những bên nào phải ngừng xử lý dữ liệu của chủ thể?',
        'Bên Kiểm soát, Bên Xử lý, Bên Kiểm soát và xử lý, và Bên thứ ba phải ngừng xử lý, đồng thời yêu cầu các tổ chức/cá nhân liên quan ngừng xử lý.',10,
        'Bên Kiểm soát đữ liệu, Bên Xử lý dữ liệu, Bên Kiêm soát và xử lý dữ liệu, Bên thứ ba phải ngừng và yêu cầu các tô chức, cá nhân có liên quan ngừng xử lý dữ liệu của chủ thê dữ liệu đã rút lại sự đông ý.',
        kind='direct'),
      answer_case('nd13-23',
        'Trong trường hợp nào bên kiểm soát có thể không cung cấp dữ liệu vì việc cung cấp có thể ảnh hưởng tới người khác?',
        'Khi việc cung cấp có thể ảnh hưởng tới sự an toàn, sức khỏe thể chất hoặc tinh thần của người khác.',11,
        'Việc cung cấp dữ liệu cá nhân của chủ thể dữ liệu có thể ảnh hưởng tới sự an toàn, sức khỏe thê chật hoặc tinh thân của người khác;',
        kind='condition'),
      answer_case('nd13-24',
        'Nếu không thể thực hiện yêu cầu chỉnh sửa dữ liệu cá nhân, sau bao lâu phải thông báo cho chủ thể dữ liệu?',
        'Sau 72 giờ kể từ khi nhận được yêu cầu chỉnh sửa.',13,
        'Trường hợp không thể thực hiện thì thông báo tới chủ thể dữ liệu sau 72 giờ kế khi nhận được yêu cầu chỉnh sửa đữ liệu cá nhân của chủ thê dữ liệu.',
        kind='condition'),
      answer_case('nd13-25',
        'Thông thường Bộ Công an kiểm tra việc chuyển dữ liệu cá nhân ra nước ngoài bao lâu một lần, và những ngoại lệ nào được nêu?',
        'Một lần mỗi năm; có thể kiểm tra khác thường khi phát hiện vi phạm quy định hoặc xảy ra sự cố lộ, mất dữ liệu cá nhân của công dân Việt Nam.',21,
        'Căn cứ tình hình cụ thể, Bộ Công an quyết định việc kiểm tra chuyển dữ liệu cá nhân ra nước ngoài 01 lần/năm, trừ trường hợp phát hiện hành vi vi phạm quy định của pháp luật về bảo vệ dữ liệu cá nhân tại Nghị định này hoặc để xảy ra sự cô lộ, mất dữ liệu cá nhân của công dân Việt Nam.',
        kind='condition'),
      {'id':'nd13-test-missing-03','split':'test','question':'Số điện thoại đường dây nóng của Cục An ninh mạng và phòng, chống tội phạm sử dụng công nghệ cao để tiếp nhận yêu cầu về dữ liệu cá nhân là số nào?',
       'filter':{},'answerable':False,'absence_reason':'Bản Nghị định không nêu số điện thoại đường dây nóng của Cục; việc nêu chi tiết liên lạc trong biểu mẫu không cung cấp số hotline của cơ quan.',
       'absence_audit_terms':['đường dây nóng','hotline','số điện thoại Cục','điện thoại liên hệ Cục']},
      {'id':'nd13-test-missing-04','split':'test','question':'Nghị định 13 ấn định ngân sách hằng năm chính xác bao nhiêu đồng cho hoạt động bảo vệ dữ liệu cá nhân của doanh nghiệp?',
       'filter':{},'answerable':False,'absence_reason':'Điều 31 quy định tổ chức, doanh nghiệp tự bố trí kinh phí nhưng không quy định một mức ngân sách hằng năm bằng đồng.',
       'absence_audit_terms':['kinh phí bảo vệ dữ liệu cá nhân của tổ chức','ngân sách nhà nước hằng năm','đồng/năm','mức kinh phí doanh nghiệp']},
    ]
    if len(dev)!=22 or len(test)!=7: raise AssertionError('Benchmark size mismatch')
    for q in dev: q['split']='dev'
    pages=load('data/nd13/pages.json')
    chunks=load('data/nd13/chunks.json')
    from src.evaluation import validate_cases
    validate_cases(chunks,dev,'dev'); validate_cases(chunks,test,'test')
    full='\n'.join(p['text'] for p in pages).casefold()
    absence=[]
    all_missing=[q for q in dev+test if not q['answerable']]
    for q in all_missing:
        results={term:full.count(term.casefold()) for term in q['absence_audit_terms']}
        absence.append({'query_id':q['id'],'question':q['question'],'audit_terms':results,
          'manual_scope':q['absence_reason'],'reviewed_pages':'All 39 OCR pages, including appendix/forms (not only retrieved context).',
          'result':'Exact requested numeric/contact fact not present; partial topical mentions recorded in query-level reason.'})
    protocol={
      'version':2,'dataset':'Day 06 Vietnamese OCR of Nghị định 13/2023/NĐ-CP',
      'source_set':'20 questions frozen by Day 06; their Day 7 runs were already inspected and are now treated as development only.',
      'dev':{'cases':22,'answerable':20,'unanswerable':2},
      'test':{'cases':7,'answerable':5,'unanswerable':2},
      'test_freeze':'The seven new test questions and absence scans were written before any new test inference. Do not tune on them.',
      'dev_reuse':'The previous 20-question, five-method traces are preserved unchanged under results/nd13/external_v1 and imported as dev with trace_origin. Four additional dev missing-evidence cases are newly run.',
      'methods':['baseline','lexical','hybrid','mmr','rerank'],
      'source_pdf_sha256':load('data/nd13/source_manifest.json')['sha256'],
      'ocr_sha256':sha256('data/nd13/pages.json'),
      'dev_sha256':None,'test_sha256':None,
      'selection':'Highest audited dev answer-grade mean with errors scored zero; tie-break correct abstention, context evidence, latency; freeze code/config/model before test.',
      'answer_quality':'Manual AI-assisted source review per case; answer/citation support are separately graded. Student review pending.',
      'external_v1_not_holdout':True,
    }
    save('benchmark/nd13/dev.json',dev); save('benchmark/nd13/test.json',test)
    protocol['dev_sha256']=sha256('benchmark/nd13/dev.json'); protocol['test_sha256']=sha256('benchmark/nd13/test.json')
    save('benchmark/nd13/protocol.json',protocol)
    save('benchmark/nd13/absence_audit.json',absence)
    print(json.dumps({'dev':len(dev),'test':len(test),'dev_answerable':sum(q['answerable'] for q in dev),
      'test_answerable':sum(q['answerable'] for q in test),'absence_audit':absence},ensure_ascii=False))

if __name__=='__main__': main()
