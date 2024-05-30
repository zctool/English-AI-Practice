window.onload = function () {
  //获取login
  let login = document.querySelector(".login");

  let span;
  let inTime, outTime;
  let isIn = true; //默认打开
  let isOut;

  //鼠标进入事件
  login.addEventListener("mouseenter", function (e) {
    isOut = false; //预先关闭，若不进入if，则不能进入鼠标离开事件的if
    if (isIn) {
      inTime = new Date().getTime();

      //生成span元素添加进login的末尾
      span = document.createElement("span");
      login.appendChild(span);

      //span去使用in动画
      span.style.animation = "in .5s ease-out forwards";

      //计算 top 和 left 值，跟踪鼠标位置
      let top = e.clientY - e.target.offsetTop;
      let left = e.clientX - e.target.offsetLeft;

      span.style.top = top + "px";
      span.style.left = left + "px";

      isIn = false;
      isOut = true;
    }
  });

  //鼠标离开事件
  login.addEventListener("mouseleave", function (e) {
    if (isOut) {
      outTime = new Date().getTime();
      let passTime = outTime - inTime;

      if (passTime < 500) {
        setTimeout(mouseleave, 500 - passTime); //已经经过的时间就不要了
      } else {
        mouseleave();
      }
    }

    function mouseleave() {
      span.style.animation = "out .5s ease-out forwards";

      //计算 top 和 left 值，跟踪鼠标位置
      let top = e.clientY - e.target.offsetTop;
      let left = e.clientX - e.target.offsetLeft;

      span.style.top = top + "px";
      span.style.left = left + "px";

      //注意：因为要等到动画结束，所以要给个定时器
      setTimeout(function () {
        login.removeChild(span);
        isIn = true; //当我们执行完鼠标离开事件里的程序，才再次打开
      }, 500);
    }
  });
};
