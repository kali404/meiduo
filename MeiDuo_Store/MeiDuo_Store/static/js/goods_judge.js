var vm = new Vue({
    el: '#app',
    // 修改Vue变量的读取语法，避免和django模板语法冲突
    delimiters: ['[[', ']]'],
    data: {
        host,
        skus: []
    },
    mounted: function(){
        // 渲染评价界面
        this.render_comments();
    },
    methods: {
        // 渲染评价界面
        render_comments(){
            this.skus = JSON.parse(JSON.stringify(skus));
            for(var i=0;i<this.skus.length;i++){
                this.skus[i].url = '/goods/' + this.skus[i].sku_id + '.html';
                Vue.set(this.skus[i], 'score', 0); // 记录随鼠标变动的星星数
                Vue.set(this.skus[i], 'display_score', 0); // 展示变动的分数值
                this.skus[i].final_score = 0; // 记录用户确定的星星数
                Vue.set(this.skus[i], 'comment', '');
                Vue.set(this.skus[i], 'is_anonymous', false);
            }
        },
        // 鼠标在评分星星上滑动
        on_stars_mouseover(index, score){
            this.skus[index].score = score;
            this.skus[index].display_score = score * 20;
        },
        // 鼠标从评分星星上离开
        on_stars_mouseout(index) {
            this.skus[index].score = this.skus[index].final_score;
            this.skus[index].display_score = this.skus[index].final_score * 20;
        },
        // 点击评分星星
        on_stars_click(index, score) {
            this.skus[index].final_score = score;
        },
        // 保存评价信息
        save_comment(index){
            var sku = this.skus[index];
            if (sku.comment.length < 5){
                alert('请填写多余5个字的评价内容');
            } else {
                var url = this.host + '/orders/comment/';
                axios.post(url, {
                        order_id: sku.order_id,
                        sku_id: sku.sku_id,
                        comment: sku.comment,
                        score: sku.final_score,
                        is_anonymous: sku.is_anonymous,
                    }, {
                        headers: {
                            'X-CSRFToken':getCookie('csrftoken')
                        },
                        responseType: 'json'
                    })
                    .then(response => {
                        if (response.data.code == '0') {
                            // 删除评价后的商品
                            this.skus.splice(index, 1);
                        } else if (response.data.code == '4101') {
                            location.href = '/login/?next=/orders/comment/';
                        } else {
                            alert(response.data.errmsg);
                        }
                    })
                    .catch(error => {
                        console.log(error.response);
                    })
            }
        }
    }
});
