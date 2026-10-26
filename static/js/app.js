const { createApp, ref, computed, onMounted, watch } = Vue;

createApp({
  setup() {
    // 视图模式与导航切换
    const currentMode = ref('customer'); // 'customer' 或 'admin'
    const customerTab = ref('ordering'); // 'ordering', 'merchant', 'reviews', 'orders'
    const adminTab = ref('admin_orders'); // 'admin_orders', 'admin_dishes', 'admin_reviews', 'admin_settings'
    const loading = ref(false);

    // 核心数据
    const merchant = ref({
      name: '拾味小馆',
      slogan: '载入中...',
      is_open: 1,
      avg_rating: 5.0,
      total_sales: 0,
      review_count: 0,
      tags: [],
      gallery: []
    });
    const categories = ref([]);
    const dishes = ref([]);
    const selectedCategory = ref(null);
    const searchQuery = ref('');
    const ordersList = ref([]);
    const reviewsList = ref([]);
    const reviewStats = ref({
      total_count: 0,
      avg_rating: 5.0,
      avg_taste: 5.0,
      avg_service: 5.0,
      stars: { 5: { count: 0, pct: 0 }, 4: { count: 0, pct: 0 }, 3: { count: 0, pct: 0 }, 2: { count: 0, pct: 0 }, 1: { count: 0, pct: 0 } }
    });
    const reviewFilter = ref('all');
    const adminStats = ref({
      today_orders: 0,
      today_revenue: 0,
      pending_orders: 0,
      total_orders: 0,
      total_revenue: 0,
      avg_rating: 5.0,
      unreplied_reviews: 0,
      top_dishes: []
    });

    // 购物车与下单状态
    const cart = ref([]);
    const isCartOpen = ref(false);
    const diningType = ref('dine_in'); // 'dine_in' or 'takeaway'
    const tableNumber = ref('A08');
    const customerName = ref('李先生');
    const customerPhone = ref('13800138000');
    const deliveryAddress = ref('南京西路1288号恒隆广场南座15楼');
    const orderRemark = ref('');
    const quickRemarks = ['免葱', '免香菜', '少辣', '不放味精', '多备餐具', '尽快出餐'];

    // 弹窗状态
    const dishModalOpen = ref(false);
    const currentDishDetail = ref(null);
    const reviewModalOpen = ref(false);
    const replyModalOpen = ref(false);
    const currentReviewToReply = ref(null);
    const replyText = ref('');
    const checkoutModalOpen = ref(false);

    // 评价表单
    const newReview = ref({
      order_id: '',
      customer_name: '',
      rating: 5,
      taste_rating: 5,
      service_rating: 5,
      content: '',
      dining_type: '堂食',
      tags: [],
      recommended_dishes: []
    });
    const availableReviewTags = ['食材新鲜', '分量足', '上菜极快', '包装精美', '环境优雅', '性价比超高', '肉质鲜嫩', '镬气十足'];

    // 商家后台：菜品编辑弹窗与表单
    const adminDishModalOpen = ref(false);
    const isEditingDish = ref(false);
    const dishForm = ref({
      id: null,
      category_id: 1,
      name: '',
      description: '',
      price: 0,
      original_price: null,
      image_url: '',
      tags: '',
      is_available: 1
    });

    // 商家后台：店铺编辑表单
    const adminMerchantForm = ref({});

    // Toast 提示工具
    const showToast = (title, icon = 'success') => {
      if (window.Swal) {
        Swal.fire({
          toast: true,
          position: 'top-end',
          icon: icon,
          title: title,
          showConfirmButton: false,
          timer: 2200,
          timerProgressBar: true
        });
      } else {
        alert(title);
      }
    };

    // 购物车计算属性
    const cartTotalQuantity = computed(() => {
      return cart.value.reduce((sum, item) => sum + item.quantity, 0);
    });

    const cartSubtotal = computed(() => {
      const sum = cart.value.reduce((total, item) => total + item.price * item.quantity, 0);
      return Math.round(sum * 100) / 100;
    });

    const packagingFee = computed(() => {
      if (diningType.value === 'takeaway' && cartTotalQuantity.value > 0) {
        return Math.min(Math.round(cartTotalQuantity.value * 1.5 * 10) / 10, 8.0);
      }
      return 0.0;
    });

    const cartGrandTotal = computed(() => {
      return Math.round((cartSubtotal.value + packagingFee.value) * 100) / 100;
    });

    // 菜品筛选
    const filteredDishes = computed(() => {
      let list = dishes.value;
      if (selectedCategory.value !== null) {
        list = list.filter(d => d.category_id === selectedCategory.value);
      }
      if (searchQuery.value && searchQuery.value.trim()) {
        const q = searchQuery.value.trim().toLowerCase();
        list = list.filter(d => 
          (d.name && d.name.toLowerCase().includes(q)) || 
          (d.description && d.description.toLowerCase().includes(q)) ||
          (d.tags && d.tags.toLowerCase().includes(q))
        );
      }
      return list;
    });

    // API 获取数据
    const fetchMerchant = async () => {
      try {
        const res = await fetch('/api/merchant');
        if (res.ok) {
          const data = await res.json();
          merchant.value = data;
          adminMerchantForm.value = { ...data };
        }
      } catch (err) {
        console.error('获取商家信息失败:', err);
      }
    };

    const fetchCategories = async () => {
      try {
        const res = await fetch('/api/categories');
        if (res.ok) {
          categories.value = await res.json();
        }
      } catch (err) {
        console.error('获取分类失败:', err);
      }
    };

    const fetchDishes = async (isAdmin = false) => {
      try {
        const url = isAdmin ? '/api/dishes?admin=true' : '/api/dishes';
        const res = await fetch(url);
        if (res.ok) {
          dishes.value = await res.json();
        }
      } catch (err) {
        console.error('获取菜品失败:', err);
      }
    };

    const fetchOrders = async () => {
      try {
        const res = await fetch('/api/orders');
        if (res.ok) {
          ordersList.value = await res.json();
        }
      } catch (err) {
        console.error('获取订单失败:', err);
      }
    };

    const fetchReviews = async () => {
      try {
        const url = `/api/reviews?filter_type=${reviewFilter.value}`;
        const res = await fetch(url);
        if (res.ok) {
          reviewsList.value = await res.json();
        }
        const statsRes = await fetch('/api/reviews/stats');
        if (statsRes.ok) {
          reviewStats.value = await statsRes.json();
        }
      } catch (err) {
        console.error('获取评价失败:', err);
      }
    };

    const fetchAdminStats = async () => {
      try {
        const res = await fetch('/api/stats/dashboard');
        if (res.ok) {
          adminStats.value = await res.json();
        }
      } catch (err) {
        console.error('获取后台统计失败:', err);
      }
    };

    // 购物车交互操作
    const addToCart = (dish) => {
      const existing = cart.value.find(item => item.dish_id === dish.id);
      if (existing) {
        existing.quantity += 1;
      } else {
        cart.value.push({
          dish_id: dish.id,
          name: dish.name,
          price: dish.price,
          quantity: 1,
          image_url: dish.image_url
        });
      }
      showToast(`已将【${dish.name}】加入购物车`);
    };

    const increaseCartItem = (item) => {
      item.quantity += 1;
    };

    const decreaseCartItem = (item) => {
      if (item.quantity > 1) {
        item.quantity -= 1;
      } else {
        const index = cart.value.indexOf(item);
        if (index > -1) {
          cart.value.splice(index, 1);
        }
      }
    };

    const getDishCartQty = (dishId) => {
      const found = cart.value.find(item => item.dish_id === dishId);
      return found ? found.quantity : 0;
    };

    const clearCart = () => {
      cart.value = [];
    };

    const openDishDetail = (dish) => {
      currentDishDetail.value = dish;
      dishModalOpen.value = true;
    };

    const addRemarkTag = (tag) => {
      if (!orderRemark.value.includes(tag)) {
        orderRemark.value = orderRemark.value ? `${orderRemark.value}，${tag}` : tag;
      }
    };

    // 提交订单
    const submitOrder = async () => {
      if (cart.value.length === 0) {
        showToast('购物车还是空的，请先挑选菜品', 'warning');
        return;
      }
      if (diningType.value === 'dine_in' && !tableNumber.value.trim()) {
        showToast('堂食点餐请填写桌号', 'warning');
        return;
      }
      if (diningType.value === 'takeaway' && !deliveryAddress.value.trim()) {
        showToast('外卖点餐请填写送达地址', 'warning');
        return;
      }
      if (!customerPhone.value.trim()) {
        showToast('请填写联系电话，方便联系', 'warning');
        return;
      }

      loading.value = true;
      try {
        const payload = {
          dining_type: diningType.value,
          table_number: diningType.value === 'dine_in' ? tableNumber.value : null,
          customer_name: customerName.value || '顾客',
          customer_phone: customerPhone.value,
          delivery_address: diningType.value === 'takeaway' ? deliveryAddress.value : null,
          remark: orderRemark.value,
          payment_method: 'wechat',
          items: cart.value.map(item => ({ dish_id: item.dish_id, quantity: item.quantity }))
        };

        const res = await fetch('/api/orders', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok) {
          showToast(`下单成功！单号: ${data.order_id}`);
          cart.value = [];
          isCartOpen.value = false;
          checkoutModalOpen.value = false;
          await fetchOrders();
          await fetchDishes(); // 刷新销量
          customerTab.value = 'orders'; // 跳转到我的订单页面
        } else {
          showToast(data.detail || '下单失败', 'error');
        }
      } catch (err) {
        showToast('网络错误，请稍后重试', 'error');
      } finally {
        loading.value = false;
      }
    };

    // 顾客取消订单
    const cancelOrder = async (orderId) => {
      if (!confirm('确定要取消此订单吗？')) return;
      try {
        const res = await fetch(`/api/orders/${orderId}/status`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: 'cancelled' })
        });
        if (res.ok) {
          showToast('订单已取消');
          await fetchOrders();
        }
      } catch (err) {
        showToast('取消失败', 'error');
      }
    };

    // 评价相关交互
    const openReviewModal = (order = null) => {
      newReview.value = {
        order_id: order ? order.id : '',
        customer_name: order ? order.customer_name : '',
        rating: 5,
        taste_rating: 5,
        service_rating: 5,
        content: '',
        dining_type: order ? (order.dining_type === 'takeaway' ? '外卖' : '堂食') : '堂食',
        tags: [],
        recommended_dishes: []
      };
      reviewModalOpen.value = true;
    };

    const toggleReviewTag = (tag) => {
      const idx = newReview.value.tags.indexOf(tag);
      if (idx > -1) {
        newReview.value.tags.splice(idx, 1);
      } else {
        newReview.value.tags.push(tag);
      }
    };

    const toggleDishRecommendation = (dishName) => {
      const idx = newReview.value.recommended_dishes.indexOf(dishName);
      if (idx > -1) {
        newReview.value.recommended_dishes.splice(idx, 1);
      } else {
        newReview.value.recommended_dishes.push(dishName);
      }
    };

    const submitReview = async () => {
      if (!newReview.value.content.trim()) {
        showToast('请输入评价内容', 'warning');
        return;
      }
      try {
        const payload = {
          order_id: newReview.value.order_id || null,
          customer_name: newReview.value.customer_name.trim() || '美食体验家',
          rating: newReview.value.rating,
          taste_rating: newReview.value.taste_rating,
          service_rating: newReview.value.service_rating,
          content: newReview.value.content,
          tags: newReview.value.tags.join(','),
          recommended_dishes: newReview.value.recommended_dishes.join(','),
          dining_type: newReview.value.dining_type
        };

        const res = await fetch('/api/reviews', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          showToast('感谢您的真实评价！');
          reviewModalOpen.value = false;
          await fetchReviews();
          await fetchMerchant(); // 更新评分统计
          customerTab.value = 'reviews';
        } else {
          showToast('评价提交失败', 'error');
        }
      } catch (err) {
        showToast('网络错误', 'error');
      }
    };

    // 商家后台交互
    const setOrderStatus = async (orderId, newStatus) => {
      try {
        const res = await fetch(`/api/orders/${orderId}/status`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: newStatus })
        });
        if (res.ok) {
          showToast(`订单状态已更新为: ${getStatusText(newStatus)}`);
          await fetchOrders();
          await fetchAdminStats();
        }
      } catch (err) {
        showToast('更新订单状态失败', 'error');
      }
    };

    const toggleDishStatus = async (dish) => {
      try {
        const res = await fetch(`/api/dishes/${dish.id}/toggle-status`, {
          method: 'PATCH'
        });
        if (res.ok) {
          const data = await res.json();
          dish.is_available = data.is_available;
          showToast(`菜品已【${data.is_available === 1 ? '上架' : '下架'}】`);
        }
      } catch (err) {
        showToast('切换菜品状态失败', 'error');
      }
    };

    const openCreateDishModal = () => {
      isEditingDish.value = false;
      dishForm.value = {
        id: null,
        category_id: categories.value.length > 0 ? categories.value[0].id : 1,
        name: '',
        description: '',
        price: 38.0,
        original_price: null,
        image_url: 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&auto=format&fit=crop&q=80',
        tags: '主厨推荐,美味',
        is_available: 1
      };
      adminDishModalOpen.value = true;
    };

    const openEditDishModal = (dish) => {
      isEditingDish.value = true;
      dishForm.value = {
        id: dish.id,
        category_id: dish.category_id,
        name: dish.name,
        description: dish.description,
        price: dish.price,
        original_price: dish.original_price,
        image_url: dish.image_url,
        tags: dish.tags,
        is_available: dish.is_available
      };
      adminDishModalOpen.value = true;
    };

    const saveDish = async () => {
      if (!dishForm.value.name.trim() || !dishForm.value.price) {
        showToast('请填写菜品名称和有效价格', 'warning');
        return;
      }
      try {
        let res;
        if (isEditingDish.value) {
          res = await fetch(`/api/dishes/${dishForm.value.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dishForm.value)
          });
        } else {
          res = await fetch('/api/dishes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dishForm.value)
          });
        }
        if (res.ok) {
          showToast(isEditingDish.value ? '菜品修改成功' : '新增菜品成功');
          adminDishModalOpen.value = false;
          await fetchDishes(true);
        }
      } catch (err) {
        showToast('保存菜品失败', 'error');
      }
    };

    const deleteDish = async (dishId) => {
      if (!confirm('确定要删除此菜品吗？')) return;
      try {
        const res = await fetch(`/api/dishes/${dishId}`, { method: 'DELETE' });
        if (res.ok) {
          showToast('菜品已删除');
          await fetchDishes(true);
        }
      } catch (err) {
        showToast('删除失败', 'error');
      }
    };

    // 商家回复评价
    const openReplyModal = (review) => {
      currentReviewToReply.value = review;
      replyText.value = review.merchant_reply || '';
      replyModalOpen.value = true;
    };

    const submitMerchantReply = async () => {
      if (!replyText.value.trim()) {
        showToast('请输入回复内容', 'warning');
        return;
      }
      try {
        const res = await fetch(`/api/reviews/${currentReviewToReply.value.id}/reply`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reply: replyText.value.trim() })
        });
        if (res.ok) {
          showToast('已成功回复顾客！');
          replyModalOpen.value = false;
          await fetchReviews();
          await fetchAdminStats();
        }
      } catch (err) {
        showToast('回复失败', 'error');
      }
    };

    // 商家更新店铺设置
    const saveMerchantSettings = async () => {
      try {
        const res = await fetch('/api/merchant', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(adminMerchantForm.value)
        });
        if (res.ok) {
          showToast('店铺设置已保存');
          await fetchMerchant();
        }
      } catch (err) {
        showToast('保存失败', 'error');
      }
    };

    const toggleOpenStatus = async () => {
      try {
        const res = await fetch('/api/merchant/toggle-open', { method: 'POST' });
        if (res.ok) {
          const data = await res.json();
          merchant.value.is_open = data.is_open;
          adminMerchantForm.value.is_open = data.is_open;
          showToast(`已切换为【${data.is_open === 1 ? '营业中' : '休息打烊'}】`);
        }
      } catch (err) {
        showToast('切换营业状态失败', 'error');
      }
    };

    // 状态工具函数
    const getStatusText = (status) => {
      const map = {
        pending: '待接单',
        preparing: '后厨制作中',
        delivering: '待取餐/配送中',
        completed: '已完成',
        cancelled: '已取消'
      };
      return map[status] || status;
    };

    const getStatusBadgeClass = (status) => {
      const map = {
        pending: 'bg-amber-100 text-amber-800 border-amber-300',
        preparing: 'bg-blue-100 text-blue-800 border-blue-300',
        delivering: 'bg-purple-100 text-purple-800 border-purple-300',
        completed: 'bg-emerald-100 text-emerald-800 border-emerald-300',
        cancelled: 'bg-slate-100 text-slate-500 border-slate-300'
      };
      return map[status] || 'bg-gray-100 text-gray-800';
    };

    // 监听评价筛选变化
    watch(reviewFilter, () => {
      fetchReviews();
    });

    // 监听模式切换
    watch(currentMode, (newMode) => {
      if (newMode === 'admin') {
        fetchDishes(true);
        fetchAdminStats();
      } else {
        fetchDishes(false);
      }
    });

    onMounted(async () => {
      await fetchMerchant();
      await fetchCategories();
      await fetchDishes();
      await fetchOrders();
      await fetchReviews();
      await fetchAdminStats();
    });

    return {
      currentMode,
      customerTab,
      adminTab,
      loading,
      merchant,
      categories,
      dishes,
      filteredDishes,
      selectedCategory,
      searchQuery,
      ordersList,
      reviewsList,
      reviewStats,
      reviewFilter,
      adminStats,

      // 购物车与结算
      cart,
      isCartOpen,
      diningType,
      tableNumber,
      customerName,
      customerPhone,
      deliveryAddress,
      orderRemark,
      quickRemarks,
      cartTotalQuantity,
      cartSubtotal,
      packagingFee,
      cartGrandTotal,
      addToCart,
      increaseCartItem,
      decreaseCartItem,
      getDishCartQty,
      clearCart,
      addRemarkTag,
      submitOrder,
      cancelOrder,

      // 弹窗与评价
      dishModalOpen,
      currentDishDetail,
      openDishDetail,
      reviewModalOpen,
      openReviewModal,
      newReview,
      availableReviewTags,
      toggleReviewTag,
      toggleDishRecommendation,
      submitReview,
      checkoutModalOpen,

      // 商家后台
      setOrderStatus,
      toggleDishStatus,
      openCreateDishModal,
      openEditDishModal,
      saveDish,
      deleteDish,
      adminDishModalOpen,
      isEditingDish,
      dishForm,
      adminMerchantForm,
      saveMerchantSettings,
      toggleOpenStatus,
      replyModalOpen,
      currentReviewToReply,
      replyText,
      openReplyModal,
      submitMerchantReply,

      // 格式化与辅助
      getStatusText,
      getStatusBadgeClass
    };
  }
}).mount('#app');
