jQuery.support.cors = true;

String.prototype.padhelper = function(totalWidth, paddingChar, isRightPadded) {
    if (this.length < totalWidth) {
        var paddingString = new String();
        for ( i = 1; i <= (totalWidth - this.length); i++) {
            paddingString += paddingChar;
        }
        if (isRightPadded) {
            return (this + paddingString);
        } else {
            return (paddingString + this);
        }
    } else {
        return this;
    }
};

Number.prototype.padLeft = function(base,chr){
    var  len = (String(base || 10).length - String(this).length)+1;
    return len > 0? new Array(len).join(chr || '0')+this : this;
};

jQuery.extend({
  chrome: function() { return navigator.userAgent.indexOf('Chrome')>0; },
  firefox: function() { return navigator.userAgent.indexOf('Firefox')>0; },
  console: function() { return window.console; },
  newguid: function() {
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
             var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
             return v.toString(16);
        });
  }
});


//round rect
CanvasRenderingContext2D.prototype.roundRect = function (x, y, w, h, r, cf, cb) {
    if (w < 2 * r) r = w / 2;
    if (h < 2 * r) r = h / 2;
    this.beginPath();
    this.moveTo(x+r, y);
    this.arcTo(x+w, y, x+w, y+h, r);
    this.arcTo(x+w, y+h, x, y+h, r);
    this.arcTo(x, y+h, x, y, r);
    this.arcTo(x, y, x+w, y, r);
    this.strokeStyle=cb;

    var grd=this.createLinearGradient(0,0,w+100,h+100);
    grd.addColorStop(0,cf);
    grd.addColorStop(1,cb);

    this.fillStyle=grd;
    this.lineWidth=1;
    this.fill();
    this.closePath();
    return this;
};

//circle
CanvasRenderingContext2D.prototype.roundCircle = function(x, y, r, c) {
    this.beginPath();
    this.arc(x,y,r,0,Math.PI*2,true);
    this.fillStyle = c;
    this.fill();
    this.closePath();
    return this;
};


function setheight(){
    $('#nav_bar_div,#selection_bar_div,#content_div').height(document.body.clientHeight-headheight);
}
