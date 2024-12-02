import pyrebase 
import json
from datetime import datetime,timezone

class DBhandler:
    def __init__(self):
        with open('authentication/firebase_auth.json') as f:
            config = json.load(f)

        firebase = pyrebase.initialize_app(config)
        self.db = firebase.database()
    
    def child(self, node_name):
        return self.db.child(node_name)
    
    # 상품 등록 
    def insert_product(self, userId, data, productImage):
        product_info = {
            "productName" : data ['productName'],
            "price" : data['price'],
            "category":data['category'],
            "location":data['location'],
            "description":data['description'],
            "productImage": productImage,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "reviewCount": 0,
            "userId": userId
        }
        
        product_ref = self.db.child("products").child(userId).push(product_info)
        productId = product_ref['name']
        # print(f"Product ID: {productId} 등록 성공") 
        # print(f"Nickname: {nickname}") #nickname이 넘어오지 않는 상태! 
        print(data, productImage)
        return True 
    

    # 상품 전체 조회 
    def get_products(self):
        products = self.db.child("products").get().val()

        flat_products={}
        for userId, userProducts in products.items():
            for productId, productData in userProducts.items():
                flat_products[productId] = productData
        return flat_products
    

    # 상품 세부 조회 -> 이름으로 조회 
    def get_product_by_id(self, productId):
        products = self.db.child("products").get().val()
        print(f"Debug: All products: {products}")  # 디버깅 로그 수정
        for userId, userProducts in products.items():
            if productId in userProducts: 
                return userProducts[productId]
        return None 
 
    #카테고리별 상품리스트 보여주기
    def get_products_bycategory(self, cate):
        items = self.db.child("product").get()
        target_value=[]
        target_key=[]
        for res in items.each():
            value = res.val()
            key_value = res.key()
            if value['category'] == cate:
                target_value.append(value)
                target_key.append(key_value)
        print("######target_value",target_value)
        new_dict={}
        for k,v in zip(target_key,target_value):
            new_dict[k]=v
        return new_dict
    #------------------------------------------------------------------------------------------   
    # 리뷰 등록 
    def insert_review(self, data, img_path):
        # 상품 정보 가져오기 
        productId = data.get("productId")

        product = self.db.child("products").child(productId).get().val() 

        # 리뷰 데이터 생성 
        review_info={
            "productId" : productId,
            "userId": data.get("userId"),  # 현재 로그인한 사용자 ID
            "title": data.get("title"),
            "content": data.get("content"),
            "rate" : data.get("rate"),
            "createdAt" : data.get("createdAt", datetime.utcnow().isoformat()),
            "reviewImage": img_path
        }
        self.db.child("reviews").push(review_info)
    
    # 리뷰 전체 조회 
    def get_reviews(self):
        reviews=self.db.child("reviews").get().val()
        return reviews
    
    # 리뷰 상세 조회
    def get_review_by_id(self, reviewId):
        review = self.db.child("reviews").child(reviewId).get().val()
        print(f"Debug: Retrieved review for reviewId {reviewId}: {review}")
        return review
    
    # 상품 별 리뷰 목록 조회 
    def get_review_by_product(self, productId):
        allReviews = self.db.child("reviews").get().val()
        if not allReviews:
            return []  # 리뷰 데이터가 없으면 빈 리스트 반환

        productReviews = []
        for reviewId, reviewData in allReviews.items():
            if reviewData and reviewData.get("productId") == productId: 
                productReviews.append({
                    "reviewId": reviewId,
                    "rate": int(reviewData.get("rate")),
                    "title": reviewData.get("title"), 
                    "content": reviewData.get("content"), 
                    "reviewImage": reviewData.get("reviewImage"),  
                    "createdAt": reviewData.get("createdAt"),  
                })

        return productReviews
    #-----------------------------------------------------------------------------------------  
    def get_heart_byname(self, uid, productName):
        hearts = self.db.child("heart").child(uid).get()
        target_value =""
        if hearts.val() == None:
            return target_value
        
        for res in hearts.each():
            key_value = res.key()
            
            if key_value == productName:
                target_value = res.val()
        return target_value
    
    def update_heart(self, userId, isHeart, productName):
        heart_info={
            "interested" : isHeart
        }
        self.db.child("heart").child(userId).child(productName).set(heart_info)
        return True

    #------------------------------------------------------------------------------------------
    # 로그인 검증 
    def find_user(self, userId, pw_hash):
        # 모든 사용자 데이터를 가져옴 
        users = self.db.child("users").get()

        # 모든 사용자 데이터에서 userId와 비밀번호 확인 
        for user in users.each():
            value = user.val()
            if value['userId'] == userId and value['pw'] == pw_hash:
                return value.get('nickname', None)
        return None
    
    # 회원가입 
    def insert_user(self, data, pw_hash, profile_image):
        user_info ={
        "userId": data['userId'],
        "pw": pw_hash,
        "nickname": data['nickname'],
        "email": data['email'],
        "phoneNum":data['phoneNum'],
        "profileImage": profile_image,
        "purchasedProducts" : {} # 빈 구매 목록 
        }

        # 사용자 중복 여부 확인 
        if self.user_duplicate_check(data['userId']):
           self.db.child("users").child(data['userId']).set(user_info)
           return True
        return False

    # 중복된 사용자 ID 체크 
    def user_duplicate_check(self, userId):
        user = self.db.child("users").child(userId).get().val()
        if user:
            return False
        return True
    
    #------------------------------------------------------------------------------------------
    # 사용자 정보 조회 
    def get_user_info(self, userId):
        user= self.db.child("users").child(userId).get().val()
        if not user:
            return None 
        return{
            "nickname":user.get("nickname"),
            "email":user.get("email"),
            "profileImage": user.get("profileImage")
        }
    
    # 구매 목록 조회 
    def get_purchased_list(self, userId):
        userPurchased = self.db.child("users").child(userId).child("purchasedProducts").get().val()

        # 구매 목록이 없으면 빈 리스트 반환 
        if not userPurchased:
            return []
        
        # 구매 목록 반환 
        return[
            {
                "productImage":item.get("productImage")
            }
            for item in userPurchased.values()
        ]

    # 판매 목록 조회 
    def get_sell_list(self, userId):
        # 사용자가 등록한 상품 데이터 가져오기 
        products = self.db.child("products").child(userId).get().val()

        # 등록된 상품이 없으면 빈 리스트 반환 
        if not products:
            return []
        # 상품 목록을 리스트로 변환 
        return[
            {
                "productImage": productData.get("productImage")
            }
            for productId, productData  in products.items()
        ]