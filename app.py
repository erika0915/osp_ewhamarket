from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
from database import DBhandler
import hashlib
import sys 

application  = Flask(__name__, static_folder='static')
application.config["SECRET_KEY"]="helloosp"
DB = DBhandler()

# 첫 화면 
@application.route("/")
def hello() :
    #return render_template("index.html")
    return redirect(url_for('view_products'))

# 전체 상품 조회 
@application.route("/products")
def view_products(): 
    page = request.args.get("page", 0, type = int) 
    per_page = 6 
    per_row = 3 
    row_count = int(per_page/per_row)

    # 데이터베이스에서 상품 가져오기 
    data = DB.get_products() 
    if not data:
        print("DB에 데이터가 없습니다.")
        return render_template("products.html", total=0, datas=[], page_count=0, m=row_count)

    # 페이지네이션 처리 
    start_idx = per_page * page
    end_idx = per_page * (page+1)
    item_counts = len(data)
    data = dict(list(data.items())[start_idx:end_idx])
    tot_count = len(data)
    for i in range(row_count):
        if (i == row_count -1) and (tot_count % per_row != 0):
            locals()['data_{}'.format(i)] = dict(list(data.items())[i*per_row:])
        else:
            locals()['data_{}'.format(i)] = dict(list(data.items())[i*per_row:(i+1)*per_row])

    return render_template(
        "products.html", 
        datas = data.items(),
        row1 = locals()['data_0'].items(), 
        row2 = locals()['data_1'].items(), 
        limit = per_page, 
        page = page, 
        page_count = int((item_counts / per_page) + 1), 
        total = item_counts, 
        m=row_count
    )

# 상품 등록
@application.route('/reg_product', methods=['GET', 'POST'])
def reg_product():
    if request.method=='GET': 
        return render_template('reg_product.html')

    elif request.method=='POST':
        # 이미지 파일 저장 
        image_file = request.files.get("productImage")
        image_file.save("static/images/{}".format(image_file.filename))

        # 폼 데이터 처리 
        data = request.form 
        print(data)

    if DB.insert_product(data['productName'], data, image_file.filename): 
        flash("상품이 성공적으로 등록되었습니다!")
        return redirect(url_for('view_products'))        
 
# 상품 상세 조회 
@application.route("/products/<name>/")
def view_product_detail(name):
    data = DB.get_product_byname(str(name))
    return render_template("product_detail.html", name= name, data=data)
#------------------------------------------------------------------------------------------
# 리뷰 전체 조회 
@application.route('/reviews')
def view_reviews():
    page = request.args.get("page", 0, type = int) # 현재 페이지 번호 
    per_page = 4 # 페이지 당 항목 수 
    per_row = 2  # 한 행에 표시할 항목 수 
    row_count = int(per_page/per_row) # 행의 개수 계산 
    
    # 데이터베이스에서 리뷰 가져오기 
    data = DB.get_reviews()
    print(data)
    if not data:
        print("DB에 데이터가 없습니다.")
        return render_template("reviews.html", total=0, datas=[], page_count=0, m=row_count)

    # 리뷰 데이터를 리스트로 변환 
    all_reviews = []
    for product, reviews in data.items():
        for review_id, review in reviews.items():
            all_reviews.append({
                "product":product,
                "review_id": review_id,
                "userId" : review.get("userId"),
                "title": review.get("title"),
                "content":review.get("content"),
                "rate" : review.get("rate"),
                "reviewImage": review.get("reviewImage")
            })

    # 페이지네이션 처리 
    start_idx = per_page * page
    end_idx = per_page * (page+1)
    paginated_reviews = all_reviews[start_idx:end_idx] # 현재 페이지 데이터 슬라이싱 

    # 행 단위로 나누기 
    rows = [paginated_reviews[i * per_row:(i + 1) * per_row] for i in range(row_count)] 
     
    # 총 리뷰 개수 및 페이지 수 계산 
    tot_count = len(all_reviews) 
    page_count = (tot_count + per_page -1)// per_page 

    return render_template(
        "reviews.html", 
        datas = paginated_reviews,
        row1=rows[0] if len(rows) > 0 else [],
        row2=rows[1] if len(rows) > 1 else [],
        limit = per_page, 
        page = page, 
        page_count = page_count,
        total = tot_count,
        m = row_count
    )

# 리뷰 상세 조회 
@application.route("/reviews/<productName>/<review_id>")
def view_review_detail(productName, review_id):
    review  = DB.get_review_by_id(productName, review_id)
    return render_template("review_detail.html", review=review)

# 리뷰 등록
@application.route("/reg_review/<productName>", methods=['GET', 'POST'])
def reg_review(productName):
    if request.method=='GET':
        return render_template("reg_review.html", productName=productName)
    
    elif request.method=='POST':

        # 리뷰 데이터 가져오기 
        data=request.form 
        userId=data.get("userId")

        # 이미지 파일 처리
        image_file = request.files.get("reviewImage")
        if not image_file or image_file.filename == '':
            return "Image upload failed or no file provided.", 400
        image_file.save(f"static/images/{image_file.filename}")

        # DB에 리뷰 등록
        DB.insert_review(productName, data, image_file.filename)
        return redirect(url_for('view_reviews'))
      
#------------------------------------------------------------------------------------------  
# 좋아요 기능 
@application.route('/show_heart/<productName>/', methods=['GET'])
def show_heart(productName):
    my_heart = DB.get_heart_byname(session['id'],productName)
    return jsonify({'my_heart':my_heart})

@application.route('/like/<productName>/', methods =['POST'])
def like(productName):
    my_heart = DB.update_heart(session['id'], 'Y', productName)
    return jsonify({'msg': '좋아요 완료!'})

@application.route('/unlike/<productName>/', methods = ['POST'])
def unlike(productName):
    my_heart = DB.update_heart(session['id'], 'N', productName)
    return jsonify({'msg': '안좋아요 완료!'})
#------------------------------------------------------------------------------------------
# 로그인 조회 
@application.route("/login")
def login():
    return render_template("login.html")

# 로그인 요청 
@application.route("/login_confirm", methods=['POST'])
def login_user():
    id_=request.form['userId']
    pw=request.form['pw']
    pw_hash = hashlib.sha256(pw.encode('utf-8')).hexdigest()
    if DB.find_user(id_,pw_hash):
        session['id']=id_
        flash("로그인 되었습니다")
        return redirect(url_for('view_products'))
    else:
        flash("Wrong ID or PW!")
        return render_template("login.html")

# 로그아웃 
@application.route("/logout")
def logout_user():
    session.clear()
    return redirect(url_for('view_products'))

# 회원가입 조회 
@application.route("/signup")
def signup():
    return render_template("signup.html")
 
# 회원가입 요청 
@application.route("/signup_post", methods=['POST'])
def register_user():
    data=request.form
    pw=request.form['pw']
    pw_hash = hashlib.sha256(pw.encode('utf-8')).hexdigest()
    if DB.insert_user(data,pw_hash):
        return render_template("login.html")
    else:
        flash("user id already exist!")
        return render_template("signup.html")

@application.route('/dynamicurl/<variable_name>/')
def DynamicUrl(variable_name):
    return str(variable_name)

if __name__ == "__main__":
    application.run(host='0.0.0.0', debug=True)


